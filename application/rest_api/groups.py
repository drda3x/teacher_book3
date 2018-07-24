#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.http.response import (
    HttpResponse,
    HttpResponseServerError,
)
from application.models import (
    GroupList,
    Groups,
    Lessons,
    PassTypes,
    Passes,
    CanceledLessons,
    TeachersSubstitution,
    User,
    Comments,
    Students,
    Debts
)
from auth import auth
from traceback import format_exc
import json
from datetime import datetime, timedelta
from django.db.models import Q

from application.common.date import get_calendar, MONTH_RUS
from application.common.lessons import (
    create_new_passes,
    process_attended_lessons,
    process_not_attended_lessons,
    process_club_cards_lessons,
    get_students_lessons,
    get_lessons_out_of_range,
    restore_database,
    delete_lessons as delete_lessons_func,
    move_lessons as move_lessons_func,
    set_substitution,
    create_debts
)

from application.common.group import (
    get_students,
    cancel_lesson as cancel_lesson_func,
    restore_lesson as restore_lesson_func,
    delete_student as delete_student_func,
    calc_group_profit,
    add_student_to_group
)

from application.common.comments import get_comments

from itertools import takewhile, chain, groupby
from collections import OrderedDict, Counter
from application.settings import TIME_ZONE
from pytz import timezone, utc


@auth
def get_list(request):
    u"""
    Функция для получения списка групп

    args:
        request django.http.request.HttpRequest

    return:
        django.http.response.HttpResponse
    """
    MAX_CLOSED_GROUPS = 5
    if request.user.is_superuser:
        groups = Groups.objects.select_related('level').all()
        closed_groups = Groups.closed.order_by("-end_date")[:MAX_CLOSED_GROUPS]

    else:
        groups = Groups.objects.select_related('level').filter(teachers=request.user)
        closed_groups = Groups.closed.filter(teachers=request.user).order_by("-end_date")[:MAX_CLOSED_GROUPS]

    data = []
    groups = sorted(groups, key=lambda x: x.level.sort_num)
    now = datetime.now().date()

    def get_info(g):
        calendar = get_calendar(now, g.days, "backward")
        days = 3

        try:
            if request.user.is_superuser:
                profit = calc_group_profit(g, [calendar.next() for i in range(days)])
                _, profit = zip(*profit)

                teachers = len(g.teachers.exclude(assistant=True))
                assistants = len(g.teachers.all()) - teachers
                assistant_sal = 500 * assistants * days
                good_profit = 1000 * teachers * days - assistant_sal
                normal_profit = 650 * teachers * days - assistant_sal

                profit = sum(profit)
                profit = 1 if profit >= good_profit else \
                        -1 if profit < normal_profit else 0
            else:
                profit = 0

        except Exception:
            profit = 0

        return dict(
            profit=profit,
            show_st=g.start_date >= now,
            **g.__json__(
                "id",
                "name",
                "dance_hall__station",
                "days",
                "time",
                "start_date"
            )
        )

    for level, groups in groupby(groups, lambda x: x.level):
        data.append(dict(
            label=level.name,
            groups=map(get_info, groups)
        ))

    data.append(dict(
        label="Закрытые группы",
        groups=map(get_info, closed_groups)
    ))

    return HttpResponse(json.dumps(data))


@auth
def get_base_info(request):
    u"""
    Функция для получения данных для одной группы
    args:
        request django.http.request.HttpRequest

    return:
        django.http.response.HttpResponse
    """

    # TODO Тут оставить только прием запроса и отправку ответа
    # TODO остальное вынести в common.group

    path = [elem for elem in request.path.split('/')[2:] if elem != u'']
    path.append(datetime.now())

    group_id, raw_date = path[:2]

    try:
        group = Groups.objects.get(pk=int(group_id))

    except Groups.DoesNotExist:
        group = Groups.closed.get(pk=int(group_id))

    date = raw_date
    if isinstance(date, (str, unicode)):
        date = datetime.strptime(raw_date, '%m%Y')

    date = max(group.start_date, date.replace(day=1).date())

    if group.end_date is not None:
        try:
            last_group_lesson = Lessons.objects.filter(group=group).order_by('date').last().date
        except AttributeError:
            last_group_lesson = group.end_date

        if date > group.end_date:
            date = group.end_date.replace(day=1)
    else:
        last_group_lesson = date + timedelta(days=100)

    dates = list(
        takewhile(
            lambda x: x.month == date.month and x <= last_group_lesson,
            get_calendar(date, group.days)
        )
    )

    canceled_dates = CanceledLessons.objects.filter(
        group=group, date__range=(dates[0], dates[-1])
    ).values_list("date", flat=True)

    students = get_students(group).order_by('last_name', 'first_name')
    inactive_students = Lessons.objects.filter(group=group, date__range=(dates[0], dates[-1])).exclude(student__in=students).values_list("student", flat=True)
    students = Students.objects.filter(Q(id__in=students.values_list("id", flat=True)) | Q(id__in=inactive_students))

    add_dates = dict(GroupList.objects.filter(
            group=group,
            student__in=students
        ).values_list("student__id", "last_update")
    )

    # now date
    now_date = datetime.now().date()

    # two weeks ago
    twa = now_date - timedelta(days=14)

    # is new group
    ing = group.start_date > twa

    check_is_new = lambda stid: ing or add_dates.get(student.id, twa) > twa
    lessons = get_students_lessons(group, dates[0], dates[-1], students)
    lessons_ofr = get_lessons_out_of_range(lessons.itervalues(), dates[-1], group)

    pass_types = PassTypes.objects.filter(
        pk__in=group.available_passes.all()
    )

    now = datetime.now().replace(day=15).date()
    month_min = max(group.start_date.replace(day=15), (now - timedelta(days=90)))

    month = takewhile(
        lambda x: x.month <= (now + timedelta(days=30)).month,
        (month_min + timedelta(days=i) for i in range(0, 150, 30))
    )
    month_list = [
       dict(label="%s %d" % (MONTH_RUS[i.month], i.year), val=i.strftime('%m%Y'))
       for i in month
    ]

    profit = calc_group_profit(group, dates)
    teachers = len(group.teachers.exclude(assistant=True))
    assistants = len(group.teachers.all()) - teachers
    assist_sal = 500 * assistants
    normal_profit = 650 * teachers
    good_profit = 1000 * teachers

    _profit = {}
    for dt, val in profit:
        if val is not None:
            val -= assist_sal
            _profit[dt] = 1 if val >= good_profit else 0 \
                if val >= normal_profit else -1

        else:
            _profit[dt] = 0
    profit = _profit

    subst = TeachersSubstitution.objects.filter(
        group=group,
        date__in=dates
    ).values_list("date", "teachers").order_by("date")

    gt = group.teachers.all()
    _t = gt.values_list("pk", flat=True)
    teachers_work = OrderedDict(( (d, map(int, _t)) for d in dates ))

    for _date, _teachers in groupby(subst, lambda x: x[0]):
        teachers_ids = map(int, filter(lambda t: t is not None, chain(*_teachers))[1::2])

        # Графа "не было"
        teachers_ids = teachers_ids + [-1] * len(_t)
        teachers_work[_date] = teachers_ids[:len(_t)]

    club_cards = Passes.objects.filter(
        student__in=students,
        pass_type__one_group_pass=False,
        start_date__lte=dates[-1],
        end_date__gte=dates[0]
    )

    comments = get_comments(group, students)

    response = {
        "selected_month": date.strftime("%m%Y"),
        "month_list": month_list,
        "group": group.__json__(
            "id", "name", "start_date", "days", "time",
            "dance_hall__prise", "dance_hall__station"
        ),
        "dates": [
            dict(
                val=d.strftime('%d.%m.%Y'),
                day=d.strftime('%d'),
                month=d.strftime('%m'),
                year=d.strftime('%Y'),
                canceled=d in canceled_dates,
                profit=profit[d]
            )
            for d in dates
        ],
        "pass_types": [
            p.__json__("id", "name")
            for p in pass_types
        ],
        "students": [
            {
                'info': dict(
                    is_new=check_is_new(student.id),
                    **student.__json__(
                        "id", "last_name", "first_name", "phone", "org"
                    )),
                'lessons': [
                    l.__json__(
                        "group_pass__color",
                        "group_pass__pass_type__id",
                        "group_pass__pass_type__lessons",
                        "group_pass__pass_type__prise",
                        "status"
                    )
                    for l in lessons[student]
                ]
            }

            for student in students
        ],
        "out_of_range_lessons": [
            l.__json__(
                "group_pass__pass_type__prise",
                "group_pass__pass_type__lessons"
            )
            for l in lessons_ofr
        ],
        "teachers": {
            "persons": [
                t.__json__("last_name", "first_name")
                for t in gt
            ],
            "cnt": teachers + assistants,
            "assistants": assistants,
            "work": teachers_work.values(),
            "list": [
                t.__json__("id", "first_name", "last_name", "assistant")
                for t in User.objects.filter(Q(teacher=True) | Q(assistant=True))
            ]
        },
        "comments": [
            {
                "student_id": c.student.id,
                "text": c.text,
                "time": c.add_date.replace(tzinfo=utc).astimezone(timezone(TIME_ZONE)).strftime('%d.%m.%Y %H:%M')
            }
            for c in comments
        ],
        "club_cards": [
            {
                "id": cc.pass_type.id,
                "student": cc.student.id,
                "start_date": cc.start_date.strftime("%d.%m.%Y"),
                "end_date": cc.end_date.strftime("%d.%m.%Y")
            }
            for cc in club_cards
        ]
    }

    return HttpResponse(json.dumps(response))


@auth
def process_lesson(request):
    u"""
    Функция для обработки занятия в группе.
    Проставляет отметки о посещенных уроках, создает новые абонементы и
    уроки к ним, обрабатывает долги

    args:
        request django.http.request.HttpRequest

    return:
        django.http.response.HttpResponse

    """
    try:
        data = json.loads(request.body)
    except Exception:
        return HttpResponseServerError("Data is not valid")

    group = Groups.objects.get(pk=data['group'])
    date = datetime.strptime(data['date'], '%d.%m.%Y')
    today = datetime.now()

    attended = [
        s
        for s in data['students']
        if s['lesson']['status'] == Lessons.STATUSES['attended']
        and s['lesson']['is_new'] is False
    ]

    not_attended = [
        s
        for s in data['students']
        if s['lesson']['status'] == Lessons.STATUSES['not_attended']
        and s['lesson']['is_new'] is False
    ]

    new_passes = [
        s for s in data['students']
        if s['lesson']['is_new'] is True
        and s['lesson']['pass_type'] > 0
    ]

    debts = [
        s for s in data['students']
        if s['lesson']['is_new'] is True
        and s['lesson']['pass_type'] == -2
    ]

    if len(new_passes) > 0:
        create_new_passes(request.user, group, date, new_passes)
        attended += new_passes

    if len(attended) > 0 and date <= today:
        process_attended_lessons(group, date, attended)
        process_club_cards_lessons(group, date, attended)

    if len(not_attended) > 0 and date <= today:
        process_not_attended_lessons(group, date, not_attended)

    if len(debts) > 0 and date <= today:
        create_debts(date, group, debts)

    if len(attended) + len(not_attended):
        restore_database(group, date, chain(attended, not_attended))

    only_id = [s['stid'] for s in new_passes]

    # TODO Наверное можно и по изящнее как-то
    dates = list(takewhile(
        lambda x: x.month == date.month,
        get_calendar(date.replace(day=1), group.days)
    ))

    date_from, date_to = dates[0::len(dates)-1]

    new_lessons = get_students_lessons(group, date_from, date_to, only_id)
    new_lessons_json = dict()
    for st, ls in new_lessons.iteritems():
        new_lessons_json[str(st)] = [l.__json__() for l in ls]

    teachers = map(int, data['teachers'])
    set_substitution(date, group, teachers)

    return HttpResponse(json.dumps(new_lessons_json))


@auth
def delete_lessons(request):
    u"""
    Функция для удаления занятий у выбранного ученика
    args:
        request django.http.request.HttpRequest

    return:
        django.http.response.HttpResponse
    """
    try:
        data = json.loads(request.body)
        date = (datetime.strptime(d, "%d.%m.%Y") for d in data['dates'])
        delete_lessons_func(date, data['stid'], data['group'])

        return HttpResponse()

    except Exception:
        return HttpResponseServerError(format_exc())


@auth
def move_lessons(request):
    u"""
    Функция для переноса занятий у выбранного ученика
    args:
        request django.http.request.HttpRequest

    return:
        django.http.response.HttpResponse
    """
    try:
        data = json.loads(request.body)
        print data
        lessons = (
            dict(
                group_pass_id=l['gpid'],
                old_date=datetime.strptime(l['old_date'], '%d%m%Y'),
                new_date=datetime.strptime(l['new_date'], '%d%m%Y')
            )
            for l in data['lessons']
        )

        move_lessons_func(lessons)
        return HttpResponse()

    except Exception:
        return HttpResponseServerError(format_exc())


@auth
def cancel_lesson(request):
    u"""
    Функция для отмены знятий
    args:
        request django.http.request.HttpRequest

    return:
        django.http.response.HttpResponse
    """
    try:
        data = json.loads(request.body)
        date = datetime.strptime(data['date'], "%d.%m.%Y")

        cancel_lesson_func(data['group'], date)

        students = get_students(data['group'])
        students_lessons = get_students_lessons(
            data['group'],
            date.replace(day=1),
            None,
            students
        )

        ordered = sorted(
            students_lessons.keys(),
            key=lambda s: (s.last_name, s.first_name)
        )

        lessons_json = [
            {
                'info': st.__json__(
                    "id", "last_name", "first_name", "phone", "org"
                ),
                'lessons': [
                    l.__json__(
                        "group_pass__color",
                        "group_pass__pass_type__id",
                        "group_pass__pass_type__lessons",
                        "group_pass__pass_type__prise",
                        "status"
                    )
                    for l in students_lessons[st]
                ]
            }
            for st in ordered
        ]

        return HttpResponse(json.dumps(lessons_json))

    except Exception:
        return HttpResponseServerError(format_exc())


@auth
def restore_lesson(request):
    u"""
    Функция для восстановления отмененых занятий
    args:
        request django.http.request.HttpRequest

    return:
        django.http.response.HttpResponse
    """

    try:
        data = json.loads(request.body)
        date = datetime.strptime(data["date"], "%d.%m.%Y")
        group = data['group']

        restore_lesson_func(group, date)

        students = get_students(data['group'])
        students_lessons = get_students_lessons(
            data['group'],
            date.replace(day=1),
            None,
            students
        )

        ordered = sorted(
            students_lessons.keys(),
            key=lambda s: (s.last_name, s.first_name)
        )

        lessons_json = [
            {
                'info': st.__json__(
                    "id", "last_name", "first_name", "phone", "org"
                ),
                'lessons': [
                    l.__json__(
                        "group_pass__color",
                        "group_pass__pass_type__id",
                        "group_pass__pass_type__lessons",
                        "group_pass__pass_type__prise",
                        "status"
                    )
                    for l in students_lessons[st]
                ]
            }
            for st in ordered
        ]

        return HttpResponse(json.dumps(lessons_json))

    except Exception:
        return HttpResponseServerError(format_exc())


@auth
def delete_student(request):
    try:
        data = json.loads(request.body)
        delete_student_func(data['group'], data['stid'])

        return HttpResponse()

    except Exception:
        return HttpResponseServerError(format_exc())


@auth
def change_group(request):
    try:
        data = json.loads(request.body)
        student = Students.objects.get(pk=data['stid'])
        old_group = data['old_group']
        new_group = Groups.objects.get(pk=data['new_group'])
        date = datetime.strptime(data['date'], "%d.%m.%Y")

        to_delete = list(Lessons.objects.filter(
            group_id=old_group,
            student=student,
            date__gte=date
        ).select_related("group_pass__pass_type"))

        skips = Counter(Lessons.objects.filter(
            group_id=old_group,
            student=student,
            status=Lessons.STATUSES['moved']
        ).values_list('group_pass', flat=True))

        delete_lessons_func(date, len(to_delete), student, old_group)
        add_student_to_group(new_group, student)

        to_delete.sort(key=lambda l: l.date)

        # Привести даты в соответствие...

        group_start_date = datetime.combine(new_group.start_date, datetime.min.time())
        shifted_date = max(date, group_start_date)

        # Неявно =(( Жаль групбай не гарантирует последовательность(
        # с другой стороны - вообще не понятно как сделать это
        # элегантно =))
        for group_pass, lessons in groupby(to_delete, lambda g: g.group_pass):
            _cnt = len(list(lessons))
            default_skips = group_pass.skips or group_pass.pass_type.skips or 0

            new_pass = dict(
                stid=student.pk,
                lesson=dict(
                    status=Lessons.STATUSES['not_processed'],
                    is_new=True,
                    pass_type=group_pass.pass_type.pk,
                    lessons_cnt=_cnt,
                    skips_cnt=default_skips - skips[group_pass.id]
                )
            )
            create_new_passes(request.user, new_group, shifted_date, new_pass)

            calendar = zip(
                get_calendar(shifted_date, new_group.days), range(_cnt)
            )
            shifted_date, _ = list(calendar)[-1]

        return HttpResponse()

    except Exception:
        return HttpResponseServerError(format_exc())


@auth
def get_group_calendar(request):
    data = json.loads(request.body)
    group_id = data['group_id']
    from_date = datetime.strptime(data['from_date'], '%m%Y')
    month_cnt = int(data['month_cnt'])
    student_id = int(data['student_id'])

    group = Groups.objects.get(pk=group_id)
    gb = groupby(get_calendar(from_date, group.days), lambda d: d.month)
    result = []

    last_lesson_date = Lessons.objects.filter(
        group_id=group_id,
        student_id=student_id
    ).latest('date').date
    lessons = get_students_lessons(group, from_date.date(), last_lesson_date, [student_id])
    lessons = lessons[student_id]
    lessons_map = dict(
        (l.date, l.__json__(
            "group_pass__color",
            "group_pass__id",
            "status"
        )) for l in lessons
    )

    next_iter_break = False

    for i, g in enumerate(gb, 1):
        month_num, days = g
        days = list(days)

        mth = dict(
            month=month_num,
            days=[
                {
                    "day": day.strftime('%d%m%Y'),
                    "lesson_data": lessons_map.get(day.date(), [None, None, None])
                }
                 for day in days
            ]
        )
        result.append(mth)

        if next_iter_break:
            break

        if days[-1].date() >= last_lesson_date:
            next_iter_break = True

    return HttpResponse(json.dumps(result))

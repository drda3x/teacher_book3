#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.http.response import (
    HttpResponse,
    HttpResponseServerError,
)
from application.models import (
    Groups,
    Lessons,
    PassTypes,
    CanceledLessons
)
from auth import auth
from traceback import format_exc
import json
from datetime import datetime, timedelta

from application.common.date import get_calendar, MONTH_RUS
from application.common.lessons import (
    create_new_passes,
    process_attended_lessons,
    process_not_attended_lessons,
    get_students_lessons,
    restore_database,
    delete_lessons as delete_lessons_func,
    move_lessons as move_lessons_func
)

from application.common.group import (
    get_students,
    cancel_lesson as cancel_lesson_func,
    restore_lesson as restore_lesson_func,
    delete_student as delete_student_func,
    calc_group_profit
)

from itertools import takewhile, chain, groupby


@auth
def get_list(request):
    u"""
    Функция для получения списка групп

    args:
        request django.http.request.HttpRequest

    return:
        django.http.response.HttpResponse
    """

    if request.user.is_superuser:
        groups = Groups.objects.all()

    else:
        groups = Groups.objects.filter(teachers=request.user)

    data = []
    groups = sorted(groups, key=lambda x: x.level.id)
    now = datetime.now().date()

    def get_info(g):
        calendar = get_calendar(now, g.days, "backward")
        days = 3

        try:
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

        except Exception:
            profit = 0

        return dict(profit=profit, show_st=g.start_date >= now, **g.__json__())

    for level, groups in groupby(groups, lambda x: x.level):
        data.append(dict(
            label=level.name,
            groups=map(get_info, groups)
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
    group = Groups.objects.get(pk=int(group_id))

    date = raw_date
    if isinstance(date, (str, unicode)):
        date = datetime.strptime(raw_date, '%m%Y')

    date = max(group.start_date, date.replace(day=1).date())

    if group.end_date is not None:
        last_group_lesson = Lessons.objects.all().order_by('date').last().date
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
    lessons = get_students_lessons(group, dates[0], dates[-1], students)

    pass_types = PassTypes.objects.filter(
        pk__in=group.available_passes.all()
    )

    now = datetime.now().replace(day=15).date()
    month_min = max(group.start_date.replace(day=15), (now - timedelta(days=90)))
    month = takewhile(
        lambda x: x <= (now + timedelta(days=30)),
        (month_min + timedelta(days=i) for i in range(0, 150, 30))
    )
    month_list = [
       dict(label="%s %d" % (MONTH_RUS[i.month], i.year), val=i.strftime('%m%Y'))
       for i in month
    ]

    response = {
        "selected_month": date.strftime("%m%Y"),
        "month_list": month_list,
        "group": group.__json__(),
        "dates": [
            dict(
                val=d.strftime('%d.%m.%Y'),
                canceled=d in canceled_dates
            )
            for d in dates
        ],
        "pass_types": [
            p.__json__()
            for p in pass_types
        ],
        "students": [
            {
                'info': student.__json__(),
                'lessons': [
                    l.__json__()
                    for l in lessons[student]
                ]
            }

            for student in students
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
    ]

    if len(new_passes) > 0:
        create_new_passes(group, date, new_passes)
        attended += new_passes

    if len(attended) > 0:
        process_attended_lessons(group, date, attended)

    if len(not_attended) > 0:
        process_not_attended_lessons(group, date, not_attended)

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
        date = datetime.strptime(data['date'], "%d.%m.%Y")
        delete_lessons_func(date, data['count'], data['stid'], data['group'])

        lessons = get_students_lessons(
            data['group'],
            date.replace(day=1),
            None,
            [data['stid']]
        )

        lessons_json = [l.__json__() for l in lessons[data['stid']]]
        return HttpResponse(json.dumps(lessons_json))

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
        date_from = datetime.strptime(data['date_from'], "%d.%m.%Y")
        date_to = datetime.strptime(data['date_to'], "%d.%m.%Y")

        move_lessons_func(date_from, date_to, data['stid'], data['group'])

        lessons = get_students_lessons(
            data['group'],
            date_from.replace(day=1),
            None,
            [data['stid']]
        )

        lessons_json = [l.__json__() for l in lessons[data['stid']]]
        return HttpResponse(json.dumps(lessons_json))

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
                'info': st.__json__(),
                'lessons': [
                    l.__json__()
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
                'info': st.__json__(),
                'lessons': [
                    l.__json__()
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

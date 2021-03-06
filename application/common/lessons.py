#!/usr/bin/env python
# -*- coding: utf-8 -*-


from collections import namedtuple, Counter, defaultdict
from django.db.models import Q
from date import get_calendar
from datetime import datetime, timedelta, date as datetime_date
from itertools import takewhile, groupby
from application.models import (
    User,
    Groups,
    Passes,
    Lessons,
    Students,
    TeachersSubstitution,
    Debts,
    PassTypes,
    CanceledLessons
)
from itertools import chain


class DefaultLesson(namedtuple("DefaultLesson", ["date", "status"])):
    u"""
        Структура для сохранения интерфейса класса
        application.models.Lessons
    """

    def __json__(self, *args):
        return dict(
            date=self.date.strftime("%d.%m.%Y"),
            status=self.status
        )


class ClubCardLesson(namedtuple("ClubCardLesson", ["date", "group_pass", "status"])):
    u"""
        Структура для сохранения интерфейса урока для клубной карты
        application.models.Lessons
    """

    def __json__(self, *args):
        return dict(
            date=self.date.strftime("%d.%m.%Y"),
            status=0,
            group_pass=dict(
                pass_type=dict(
                    id=self.group_pass.pass_type.id,
                    lessons=self.group_pass.pass_type.lessons,
                    prise=self.group_pass.pass_type.prise,
                ),
                color=self.group_pass.color
            )
        )


# Структура для объединения
# application.models.Students и application.models.PassTypes
PassTypeStudent = namedtuple("PassTypeStudent", ["student", "pass_type"])


class LessonsCrossException(Exception):
    pass


def get_students_lessons(group, date_from, date_to, students):
    u"""
        Функция для получения списка уроков и долгов для заданного
        списка учеников

        args:
            group application.models.Groups
            date datetime.datetime
            students [application.models.Students] or [int]

        return: {
            application.models.Students: [application.models.Lessons or DefaultLesson],
            application.models.Students: [application.models.Lessons or DefaultLesson]
        }
    """
    all_is_Students = all(isinstance(x, Students) for x in students)
    all_is_ints = all(isinstance(x, int) for x in students)

    assert all_is_Students or all_is_ints
    assert isinstance(group, (Groups, int))

    if isinstance(group, int):
        group = Groups.objects.get(pk=group)

    date_from = date_from.date() if isinstance(date_from, datetime) else date_from
    date_from = max(date_from, group.start_date)

    if date_to is not None:
        dt = date_to.date() if isinstance(date_to, datetime) else date_to
        _dates = list(takewhile(
            lambda x: x <= dt,
            get_calendar(date_from, group.days)
        ))
    else:
        _dates = list(takewhile(
            lambda x: x.month == date_from.month,
            get_calendar(date_from, group.days)
        ))
        date_to = _dates[-1]

    lessons = Lessons.objects.filter(
        group=group,
        date__range=(_dates[0], _dates[-1])
    ).exclude(status=Lessons.STATUSES['canceled'])

    club_cards = Passes.objects.filter(
        start_date__lte=date_to,
        end_date__gte=date_from
    )

    all_debts = Debts.objects.filter(
        date__in=_dates,
        group=group
    )

    if all_is_Students:
        lessons = lessons.filter(student__in=students)
        club_cards = club_cards.filter(student__in=students)
        club_cards = dict(
            (c.student, c)
            for c in club_cards
        )
        all_debts = all_debts.filter(student__in=students)

    else:
        lessons = lessons.filter(student_id__in=students)
        club_cards = club_cards.filter(student_id__in=students)
        club_cards = dict(
            (c.student.id, c)
            for c in club_cards
        )
        all_debts = all_debts.filter(student_id__in=students)

    all_debts_list = all_debts.values_list('student', 'date')

    if isinstance(date_from, datetime):
        dates = set(d.date() for d in _dates)
    else:
        dates = set(d for d in _dates)

    lessons_map = defaultdict(list)

    for lesson in lessons:
        key = lesson.student if all_is_Students else lesson.student.id
        lessons_map[key].append(lesson)

    for student in students:
        cc = club_cards.get(student)
        # Убираем клубные карты. Вообще-то тут надо было бы
        # выпилить весь запрос...
        cc = None

        if all_is_Students:
            debts_days = [d for d in dates if (student.id, d) in all_debts_list]
        else:
            debts_days = [d for d in dates if (student, d) in all_debts_list]

        _dates = dates - set(l.date for l in lessons_map[student]) - set(debts_days)

        fl = [
            ClubCardLesson(_date, cc, 0) if cc and cc.start_date <= _date <= cc.end_date else DefaultLesson(_date, -2)
            for _date in _dates
        ]

        dl = [DefaultLesson(_date, -1) for _date in debts_days]

        lessons_map[student] += fl
        lessons_map[student] += dl
        lessons_map[student].sort(key=lambda x: x.date)

    return lessons_map


def get_lessons_out_of_range(all_lessons, date_from, group):
    u"""
       Функция для получения уроков, за которые было заплачено
       в текущем месяце, но даты которых выходят за рамки текущего месяца
    """


    passes = set((
        ll.group_pass for sl in all_lessons for ll in sl
        if isinstance(ll, Lessons)
    ))

    lessons_out_of_range = Lessons.objects.filter(
        date__gt=date_from, group=group
    ).exclude(status=Lessons.STATUSES['canceled'])

    return lessons_out_of_range


def create_new_passes(user, group, date, data):
    u"""
        Функция для создания и сохранения абонементов в БД

        args:
            group application.models.Groups
            data datetime.datetime
            data [{
                stid: int,
                lesson: {
                    status: application.models.Lessons.STATUSES,
                    is_new: bool
                    pass_type: int
                    lessons_cnt: int
                    skips_cnt: int
                }
            }] or {
                stid: int,
                lesson: {
                    status: application.models.Lessons.STATUSES,
                    is_new: bool
                    pass_type: int
                    lessons_cnt: int
                    skips_cnt: int
                }
            }
    """

    if isinstance(data, dict):
        data = [data]

    assert isinstance(group, Groups)
    assert isinstance(date, datetime)
    assert all(st['lesson']['is_new'] for st in data)

    existed_lessons = Lessons.objects.filter(group=group, date__gte=date) \
        .values_list("student", "date")

    canceled_lessons = CanceledLessons.objects.filter(
        date__gte=date,
        group=group
    ).values_list("date", flat=True)

    to_delete = []

    try:
        for student in data:
            lessons_params = {}
            lessons_cnt = student['lesson'].get('lessons_cnt')
            skips_cnt = student['lesson'].get('skips_cnt')

            if lessons_cnt is not None:
                lessons_params['lessons'] = lessons_cnt

            if skips_cnt is not None:
                lessons_params['skips'] = skips_cnt

            cc_passes = PassTypes.objects.filter(
                one_group_pass=False
            ).values_list("id", flat=True)

            if student['lesson']['pass_type'] in cc_passes:
                lessons_params['end_date'] = date + timedelta(days=30)

            p = Passes(
                group=group,
                start_date=date,
                student_id=student['stid'],
                pass_type_id=student['lesson']['pass_type'],
                opener=user,
                **lessons_params
            )

            p.save()
            to_delete.append(p)

            debts = Debts.objects.filter(
                group=group, student_id=student['stid']
            ).values_list('date', flat=True)

            cnt = p.lessons if p.one_group_pass else 1

            # Не списываем долги если занятий в абонементе всего одно
            if p.lessons == 1:
                cal = get_calendar(date, group.days)
            else:
                checked_calendar = (
                    d.date() for d in get_calendar(date, group.days)
                    if d.date() not in debts
                )
                cal = chain(debts, checked_calendar)

            while cnt > 0:
                _date = cal.next()
                _date = _date if isinstance(_date, datetime_date) else _date.date()

                is_canceled = _date in canceled_lessons

                if (student['stid'], _date) in existed_lessons:
                    raise LessonsCrossException(
                        '%d %s' % (student['stid'], _date.strftime('%d.%m.%Y'))
                    )

                status = Lessons.STATUSES['not_processed']
                if is_canceled:
                    status = Lessons.STATUSES['canceled']
                elif _date in debts:
                    status = Lessons.STATUSES['attended']

                _l = Lessons(
                    date=_date,
                    student_id=student['stid'],
                    group=group,
                    group_pass=p,
                    status=status
                )

                _l.save()
                to_delete.append(_l)

                if not is_canceled:
                    cnt -= 1

                if _date in debts:
                    Debts.objects.filter(
                        group=group, student_id=student['stid'], date=_date
                    ).delete()

    except LessonsCrossException as e:
        for elem in to_delete:
            elem.delete()

        raise e


def process_attended_lessons(group, date, lessons):
    u"""
    Функция для простановки посещенных занятий

    args:
        group application.models.Groups
        date datetime.datetime
        lessons [{
            stid: int,
            lesson: {
                status: application.models.Lessons.STATUSES,
                is_new: bool
                pass_type: int
            }
        }]
    """

    assert isinstance(group, Groups)
    assert isinstance(date, datetime)

    Lessons.objects.filter(
        group=group,
        date=date,
        student_id__in=[s['stid'] for s in lessons]
    ).update(status=Lessons.STATUSES['attended'])


def process_club_cards_lessons(group, date, lessons):
    u"""
    Функция для обработки уроков по клубным картам

    args:
        group application.models.Groups
        date datetime.datetime
        lessons[{
            stid: int,
            lesson: {
                status: application.models.Lessons.STATUSES,
                is_new: bool,
                pass_type: int
            }
        }]
    """
    cards = dict(
        (p.student.id, p) for p in Passes.objects.filter(
            pass_type__one_group_pass=False,
            student__in=[s['stid'] for s in lessons],
            start_date__lte=date,
            end_date__gte=date
        )
    )

    all_lessons = defaultdict(list)
    for lesson in Lessons.objects.filter(group_pass__in=cards.values()):
        all_lessons[lesson.group_pass].append(lesson)

    for lesson in lessons:
        try:
            card = cards[lesson['stid']]
            existed_lessons = all_lessons[card]

            if len(existed_lessons) >= card.pass_type.lessons:
                continue

            new_lesson, created = Lessons.objects.get_or_create(
                student=card.student,
                group_pass=card,
                date=date,
                group=group,
                status=Lessons.STATUSES['attended']
            )

            new_lesson.save()

        except KeyError:
            continue


def process_not_attended_lessons(group, date, lessons):
    u"""
    Функция для отмечания пропусков и непосещенных занятий

    args:
        group application.models.Groups
        date datetime.datetime
        lessons [{
            stid: int,
            lesson: {
                status: application.models.lessons.statuses,
                is_new: bool
                pass_type: int
            }
        }]
    """

    Data = namedtuple("LessonData", ['student', 'pid', 'skips', 'org'])
    data = [
        Data(*l)
        for l in Lessons.objects.filter(
            group=group,
            date=date,
            student_id__in=[s['stid'] for s in lessons]
        ).select_related().values_list(
            'student',
            'group_pass__id',
            'group_pass__pass_type__skips',
            'student__org'
        )
    ]

    # TODO Вот тут почему-то генерятся два запроса
    missed_lessons = Counter(
        Lessons.objects.filter(
            group_pass_id__in=[l.pid for l in data],
            status=Lessons.STATUSES['moved'],
            date__lte=date
        ).values_list('student', flat=True)
    )

    not_attended = [
        int(s.student)
        for s in data if not s.org and s.skips <= missed_lessons[s.student]
    ]
    moved = [
        s.student
        for s in data if s.org or s.skips > missed_lessons[s.student]
    ]

    Lessons.objects.filter(
        group=group,
        date=date,
        student_id__in=not_attended
    ).update(status=Lessons.STATUSES['not_attended'])

    Lessons.objects.filter(
        group=group,
        date=date,
        student_id__in=moved
    ).update(status=Lessons.STATUSES['moved'])


def restore_database(group, date, students):
    u"""
    Функция для проверки и восстановления равновесия БД
    Проверяет чтобы количество уроков соответствовало
    количеству указанному в типе абонемента с учетом всех про
    пусков, переносов и тд

    args:
        group application.models.Groups
        date datetime.datetime
        students [{
            stid: int,
            lesson: {
                status: application.models.lessons.statuses,
                is_new: bool
                pass_type: int
            }
        }]
    """
    passes = Lessons.objects.filter(
        student_id__in=[s['stid'] for s in students],
        group=group,
        date=date,
        group_pass__pass_type__one_group_pass=True
    ).select_related('group_pass')

    lessons = Lessons.objects.filter(
        group=group,
        group_pass__in=passes.values_list('group_pass', flat=True)
    ).order_by('date')

    for p in passes.only('group_pass'):
        my_lessons = [
            l for l in lessons if l.group_pass == p.group_pass
        ]
        misses = [
            l for l in my_lessons
            if l.status == Lessons.STATUSES['moved']
        ]

        # Находим и заменяем перенесенные уроки на не посещенные
        # и наоборот, если нжуно
        delta = len(misses) - (p.group_pass.pass_type.skips or 0)
        if delta > 0:
            to_change = [
                l
                for l in my_lessons
                if l.status == Lessons.STATUSES['moved'] and l.date > date.date()
            ][:delta]

            for l in to_change:
                l.status = Lessons.STATUSES['not_attended']
                l.save()

        elif delta < 0:
            to_change = [
                l
                for l in my_lessons
                if l.status == Lessons.STATUSES['not_attended'] and l.date > date.date()
            ][:abs(delta)]

            for l in to_change:
                l.status = Lessons.STATUSES['moved']
                l.save()

        to_check = [
            l for l in my_lessons
            if l.status not in (Lessons.STATUSES['moved'], Lessons.STATUSES['canceled'])
        ]
        delta = len(to_check) - p.group_pass.lessons_origin

        if delta > 0:
            for l in my_lessons[-delta:]:
                l.delete()
        elif delta < 0:
            last_lesson = Lessons.objects.filter(group_pass=p.group_pass).latest('date')
            _date = last_lesson.date + timedelta(days=1)
            dates = zip(range(abs(delta)), get_calendar(_date, group.days))
            for _, _date in dates:
                Lessons(
                    group=group,
                    date=_date,
                    student=p.student,
                    group_pass=p.group_pass
                ).save()

    debts = Debts.objects.filter(group=group)
    d_dates = debts.values_list('id', 'student', 'date')

    if len(d_dates) > 0:
        _, student, date = d_dates[0]
        q = Q(student_id=student, date=date)

        for _, student, date in d_dates[1:]:
            q |= Q(student_id=student, date=date)

        lessons = Lessons.objects.filter(q).values_list('student', 'date')
        ids = (
            i[0] for i in d_dates if (i[1], i[2]) in lessons
        )

        debts.filter(id__in=ids).delete()


def delete_lessons(date_from, student_id, group_id):

    lessons = Lessons.objects.filter(
        date__in=date_from,
        student_id=student_id,
        group_id=group_id
    ).select_related('group_pass').order_by('date')

    passes_to_edit = set()
    lessons_to_delete = list()

    for lesson in lessons:
        passes_to_edit.add(lesson.group_pass)
        lesson.group_pass.lessons -= 1
        lessons_to_delete.append(lesson.pk)

    Lessons.objects.filter(pk__in=lessons_to_delete).delete()
    passes_to_delete = [p.pk for p in passes_to_edit if p.lessons <= 0]

    if len(passes_to_delete) > 0:
        Passes.objects.filter(
            pk__in=[p.pk for p in passes_to_edit if p.lessons <= 0]
        ).delete()


def move_lessons(lessons):
    to_save = []

    for lesson in lessons:
        new_lesson = Lessons.objects.get(
            group_pass_id=lesson['group_pass_id'],
            date=lesson['old_date']
        )

        new_lesson.date = lesson['new_date']
        to_save.append(new_lesson)

    for lesson in to_save:
        lesson.save()


def set_substitution(date, group, teachers):
    u"""
    Функция для простановки замен преподавателей

    args:
        date datetime.datetime
        group application.models.Groups or int
        teachers [application.models.User or int]
    """

    assert isinstance(group, (Groups, int))
    assert isinstance(date, datetime)
    assert all(isinstance(t, (int, User)) for t in teachers)

    if isinstance(group, int):
        group = Groups.objects.get(pk=group)

    if all(isinstance(t, User) for t in teachers):
        group_teachers = group.teachers.all()
    else:
        group_teachers = group.teachers.all().values_list("pk", flat=True)

    if all(t in group_teachers for t in teachers):
        TeachersSubstitution.objects.filter(group=group, date=date).delete()
    else:
        ts, created = TeachersSubstitution.objects.get_or_create(group=group, date=date)
        if created:
            ts.save()

        ts.teachers.clear()
        ts.teachers.add(*teachers)



def create_debts(date, group, debts):
    u"""
    Функция для создания долгов

    args:
        date datetime.datetime
        group application.models.Groups or int
        debts [
            stid: int,
            lesson: {
                status: application.models.lessons.statuses,
                is_new: bool
                pass_type: int
            }
        ]
    """

    assert isinstance(date, datetime)
    assert isinstance(group, (Groups, int))

    group_param = {}
    if isinstance(group, int):
        group_param['group_id'] = group
    else:
        group_param['group'] = group

    for debt in debts:
        new_debt = Debts(
            date=date,
            student_id=debt['stid'],
            val=0,
            **group_param
        )
        new_debt.save()


def delete_debts(date, group, students):
    u"""
    Функция для списания долгов

    args:
        date datetime.datetime
        group application.models.Groups or ints
        students [
            application.models.Students or ints
        ]
    """

    assert isinstance(date, datetime)
    assert isinstance(group, (Groups, int))
    assert all(isinstance(student, (Students, int)) for student in students)

    query_params = {}

    query_params['date'] = date

    if isinstance(group, int):
        query_params['group_id'] = group
    else:
        query_params['group'] = group

    if all(isinstance(s, int) for s in students):
        query_params['student_id__in'] = students

    else:
        query_params['student__in'] = students

    Debts.objects.filter(**query_params).delete()


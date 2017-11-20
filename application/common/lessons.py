#!/usr/bin/env python
# -*- coding: utf-8 -*-


from collections import namedtuple, Counter, defaultdict
from date import get_calendar
from datetime import datetime, timedelta
from itertools import takewhile
from application.models import Groups, Passes, Lessons, PassTypes, Students

class DefaultLesson(namedtuple("DefaultLesson", ["date", "status"])):
    u"""
        Структура для сохранения интерфейса класса
        application.models.Lessons
    """

    def __json__(self):
        return dict(
            date=self.date.strftime("%d.%m.%Y"),
            status=self.status
        )


# Структура для объединения
# application.models.Students и application.models.PassTypes
PassTypeStudent = namedtuple("PassTypeStudent", ["student", "pass_type"])


class LessonsCrossException(Exception):
    pass


def get_students_lessons(group, date_from, date_to, students):
    u"""
        Функция для получения списка уроков для заданного
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

    #group_lessonos
    lessons = Lessons.objects.filter(
        group=group,
        date__range=(date_from, date_to)
    )

    if all_is_Students:
        lessons = lessons.filter(student__in=students)
    else:
        lessons = lessons.filter(student_id__in=students)

    _dates = takewhile(
        lambda x: x <= date_to,
        get_calendar(date_from, group.days)
    )

    if isinstance(date_from, datetime):
        dates = set(d.date() for d in _dates)
    else:
        dates = set(d for d in _dates)

    lessons_map = defaultdict(list)
    for lesson in lessons:
        key = lesson.student if all_is_Students else lesson.student.id
        lessons_map[key].append(lesson)

    for student in students:
        _dates = dates - set(l.date for l in lessons_map[student])
        fl = [DefaultLesson(_date, -2) for _date in _dates]

        lessons_map[student] += fl
        lessons_map[student].sort(key=lambda x: x.date)

    return lessons_map


def create_new_passes(group, date, data):
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
                }
            }]
    """

    assert isinstance(group, Groups)
    assert isinstance(date, datetime)
    assert all(st['lesson']['is_new'] for st in data)

    existed_lessons = Lessons.objects.filter(group=group, date__gte=date) \
        .values_list("student", "date")

    to_delete = []

    try:
        for student in data:
            p = Passes(
                group=group,
                start_date=date,
                student_id=student['stid'],
                pass_type_id=student['lesson']['pass_type']
            )

            p.save()
            to_delete.append(p)

            cnt = p.lessons if p.one_group_pass else 1
            dl = zip(get_calendar(date, group.days), range(cnt))

            for _date, _ in dl:

                if (student['stid'], _date.date()) in existed_lessons:
                    raise LessonsCrossException(
                        '%d %s' % (student['stid'], _date.strftime('%d.%m.%Y'))
                    )

                l = Lessons(
                    date=_date,
                    student_id=student['stid'],
                    group=group,
                    group_pass=p
                )

                l.save()
                to_delete.append(l)

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

    qs = Lessons.objects.filter(
        group=group,
        date=date,
        student_id__in=not_attended
    ).update(status=Lessons.STATUSES['not_attended'])

    qs = Lessons.objects.filter(
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
        date=date
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
            if l.status != Lessons.STATUSES['moved']
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

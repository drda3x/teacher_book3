#!/usr/bin/env python
# -*- coding: utf-8 -*-


from application.models import (
    GroupList,
    Groups,
    Students,
    Lessons,
    CanceledLessons
)
from application.common.date import get_calendar
from django.db.models import Max
from datetime import timedelta, datetime, date as date_cls
from itertools import groupby


def add_student_to_group(group, student):
    u"""
    Функция для добавления ученика в группу

    args:
        group application.models.Groups
        student application.models.Students
    """
    try:
        group_list = GroupList.objects.get(student=student, group=group)

        if not group_list.active:
            group_list.active = True
            group_list.save()

    except GroupList.DoesNotExist:
        group_list = GroupList(
            student=student,
            group=group,
            active=True
        )

        group_list.save()


def delete_student(group, student):
    u"""
    Функция для удаления ученика из группы

    args:
        group application.models.Groups or int
        student application.models.Students or int
    """
    assert isinstance(group, (int, Groups))
    assert isinstance(student, (int, Students))

    qs_params = {}

    if isinstance(group, int):
        qs_params['group_id'] = group
    else:
        qs_params['group'] = group

    if isinstance(student, int):
        qs_params['student_id'] = student
    else:
        qs_params['student'] = student

    GroupList.objects.filter(**qs_params).update(active=False)


def get_students(group):
    u"""
    Функция для получения списка студентов для заданной группы

    args:
        group application.models.Groups

    return:
        queryset
    """

    assert isinstance(group, (Groups, int))

    params = {"active": True}
    if isinstance(group, int):
        params['group_id'] = group
    else:
        params['group'] = group

    students = Students.objects.filter(
        pk__in=GroupList.objects.filter(
            **params
        ).values_list("student", flat=True)
    ).order_by("last_name", "first_name")

    return students


def cancel_lesson(group, date):
    u"""
    Функция для отмены занятий

    args:
        group application.models.Groups or int
        date datetime.datetime
    """

    assert isinstance(group, (Groups, int))

    if isinstance(group, int):
        group = Groups.objects.get(pk=group)

    today_lessons = Lessons.objects.filter(
        group=group,
        date=date
    )

    lessons = Lessons.objects.filter(
        group_pass__in=today_lessons.values_list("group_pass", flat=True)
    )

    max_lessons = lessons.values("group_pass", "student").annotate(max_date=Max("date"))
    for lesson in max_lessons:
        date_from = lesson['max_date'] + timedelta(days=1)
        new_date = get_calendar(date_from, group.days).next()
        new_lesson = Lessons(
            student_id=lesson['student'],
            group=group,
            group_pass_id=lesson['group_pass'],
            date=new_date
        )

        new_lesson.save()

    today_lessons.update(status=Lessons.STATUSES['canceled'])
    CanceledLessons(group=group, date=date).save()


def restore_lesson(group, date):
    u"""
    Функция для восстановления отмененных занятий

    args:
        group application.models.Groups or int
        date datetime.datetime
    """

    assert isinstance(group, (Groups, int))

    if isinstance(group, int):
        group = Groups.objects.get(pk=group)

    today_lessons = Lessons.objects.filter(
        group=group,
        date=date,
        status=Lessons.STATUSES['canceled']
    )

    lessons = Lessons.objects.filter(
        group_pass__in=today_lessons.values_list("group_pass", flat=True)
    ).order_by("student", "-date")

    to_delete = [
        g.next().pk
        for k, g in groupby(lessons, lambda x: x.student)
    ]

    CanceledLessons.objects.get(group=group, date=date).delete()
    Lessons.objects.filter(pk__in=to_delete).delete()
    today_lessons.update(status=Lessons.STATUSES['not_processed'])


def calc_group_profit(group, dates):
    u"""
    Функция для расчета эффективности группы за выбраный временной
    промежуток

    args:
        group application.models.Groups or int
        date_range [datetime.datetime]

    return zip(datetime.datetime, bool or None)
    """

    assert isinstance(group, (Groups, int))
    assert all(isinstance(d, (datetime, date_cls)) for d in dates)

    if isinstance(group, int):
        params = dict(group_id=group)
    else:
        params = dict(group=group)

    params['date__in'] = dates
    lessons = sorted(
        Lessons.objects.filter(**params).exclude(status=Lessons.STATUSES['not_processed']),
        key=lambda l: l.date
    )

    vals = dict(zip(dates, [None] * len(dates)))
    for date, lessons in groupby(lessons, lambda l: l.date):
        vals[date] = sum(l.prise() for l in lessons) - group.dance_hall.prise
        vals[date] -= vals[date] * 0.3
        vals[date] = max(0, vals[date])

    return vals.iteritems()

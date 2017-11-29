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
from datetime import timedelta


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
    )

    return students


def cancel_lesson(group, date):
    u"""
    Функция для отмены занятий

    args:
        group application.models.Groups
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

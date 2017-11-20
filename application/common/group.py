#!/usr/bin/env python
# -*- coding: utf-8 -*-


from application.models import GroupList, Groups, Students


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

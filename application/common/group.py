#!/usr/bin/env python
# -*- coding: utf-8 -*-


from application.models import GroupList


def add_student_to_group(group, student):
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

#!/usr/bin/env python
# -*- coding: utf-8 -*-


from application.models import Groups, Comments, Students
from django.db.models.query import QuerySet


def get_comments(group, students):
    u"""
    Функция для получения списка коментариев
    """

    g_params = {
        int: {'group_id': group},
        Groups: {'group': group},
    }

    s_params = {
        int: {'student_id': students},
        Students: {'student': students},
        list: {'student_id__in': students},
        QuerySet: {'student__in': students}
    }

    params = dict()
    params.update(g_params[type(group)])
    params.update(s_params[type(students)])

    return Comments.objects.filter(**params).order_by("-add_date")

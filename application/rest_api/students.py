#!/usr/bin/env python
# -*- coding: utf-8 -*-

from auth import auth
from django.http import HttpResponse, HttpResponseServerError

from application.models import Groups
from application.common.students import edit_student as edit_func
from application.common.lessons import get_students_lessons, DefaultLesson
from application.common.group import add_student_to_group
from datetime import datetime

import json


@auth
def edit_student(request):
    u"""
    Функция-обработчик запроса об изменении данных ученика

    args:
        request django.http.HttpReqest

    return:
        django.http.HttpResponse
    """

    try:
        data = json.loads(request.body)
    except ValueError:
        return HttpResponseServerError('JSON is not valid')

    try:
        student = edit_func(
            data.get('stid'),
            data['phone'],
            data['name'],
            data['last_name'],
            data.get('org_status', False)
        )
    except Exception:
        from traceback import format_exc
        return HttpResponseServerError(format_exc())

    date = datetime.strptime(data['date'], '%d.%m.%Y')
    group = Groups.objects.get(pk=data['group'])

    just_added = add_student_to_group(group, student)

    lessons = get_students_lessons(
        group, date, None, [student]
    )[student]

    response = {
        'info': dict(
            is_new=just_added,
            **student.__json__("first_name", "last_name", "phone", "id")
        ),
        'lessons': [
            l.__json__(
                "group_pass__color",
                "group_pass__pass_type__id",
                "group_pass__pass_type__lessons",
                "group_pass__pass_type__prise",
                "status"
            )
            for l in lessons
        ]
    }

    return HttpResponse(json.dumps(response))

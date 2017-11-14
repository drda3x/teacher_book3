#!/usr/bin/env python
# -*- coding: utf-8 -*-

from auth import auth
from application.utils.lessons import DefaultLesson
from django.http import HttpResponse, HttpResponseServerError

import common
import json


@auth
def edit_student(request):
    try:
        data = json.loads(request.body)
    except ValueError:
        return HttpResponseServerError('JSON is not valid')

    try:
        student = common.students.edit_student(
            data.get('stid'),
            data['phone'],
            data['name'],
            data['last_name'],
            data['org_status']
        )
    except Exception:
        return HttpResponseServerError('Student data process error')

    lessons = common.lessons.get_students_lessons(
        data['group'], data['date'], [student]
    )

    response = {
        'info': student.__json__(),
        'lessons': [
            l.__json__()
            for l in lessons
        ]
    }

    return HttpResponse(json.dumps(response))

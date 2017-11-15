#!/usr/bin/env python
# -*- coding: utf-8 -*-

from auth import auth
from application.utils.lessons import DefaultLesson
from django.http import HttpResponse, HttpResponseServerError

from application.models import Groups
from application.common.students import edit_student as edit_func
from application.common.lessons import get_students_lessons
from datetime import datetime

import json


@auth
def edit_student(request):
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
            data['org_status']
        )
    except Exception:
        from traceback import format_exc
        return HttpResponseServerError(format_exc())#'Student data process error')

    date = datetime.strptime(data['date'], '%d.%m.%Y')
    group = Groups.objects.get(pk=data['group'])
    lessons = get_students_lessons(
        group, date, [student]
    )

    response = {
        'info': student.__json__(),
        'lessons': [
            l.__json__()
            for l in lessons
        ]
    }

    return HttpResponse(json.dumps(response))

#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.contrib.sessions.backends.db import SessionStore
from django.contrib import auth
from django.http.response import (
    HttpResponse,
    HttpResponseServerError,
    HttpResponseForbidden
)
from application.models import (
    Groups,
    GroupLevels,
    GroupList,
    Students,
    User,
    Lessons,
    PassTypes
)
from auth import auth
from traceback import format_exc
import json
from datetime import datetime, timedelta
from application.utils.date_api import get_calendar
from application.utils.lessons import DefaultLesson
from collections import defaultdict, namedtuple
from itertools import takewhile


@auth
def get_list(request):
    data = [
        g.__json__()
        for g in Groups.objects.all()
    ]

    return HttpResponse(json.dumps(data))


@auth
def get_base_info(request):

    path = [elem for elem in request.path.split('/')[2:] if elem != u'']
    path.append(datetime.now())

    group_id, date = path[:2]
    group = Groups.objects.get(pk=int(group_id))

    if isinstance(date, (str, unicode)):
        date = datetime.strptime(date, '%m%Y')

    date = max(group.start_date, date.replace(day=1).date())

    if group.end_date is not None:
        last_group_lesson = Lessons.objects.all().order_by('date').last().date
    else:
        last_group_lesson = date + timedelta(days=100)

    dates = list(
        takewhile(
            lambda x: x.month == date.month and x <= last_group_lesson,
            get_calendar(date, group.days)
        )
    )

    students = Students.objects.filter(
        pk__in=GroupList.objects.filter(
            group_id=group_id,
            active=True
        ).values_list('student')
    ).order_by('last_name', 'first_name')

    lessons = Lessons.objects.filter(
        group=group,
        date__range=(dates[0], dates[-1])
    ).order_by('student', 'date')

    lessons_map = defaultdict(list)

    for lesson in lessons:
        lessons_map[lesson.student].append(lesson)

    for student in students:
        _dates = set(l.date for l in lessons_map[student])
        for date in set(dates) - _dates:
            lessons_map[student].append(DefaultLesson(date, -2))

    pass_types = PassTypes.objects.filter(
        pk__in=group.available_passes.all()
    )

    response = {
        "group": group.__json__(),
        "dates": [d.strftime('%d.%m.%Y') for d in dates],
        "pass_types": [
            p.__json__()
            for p in pass_types
        ],
        "students": [
            {
                'info': student.__json__(),
                'lessons': [
                    l.__json__()
                    for l in lessons_map[student]
                ]
            }

            for student in students
        ]
    }


    return HttpResponse(json.dumps(response))

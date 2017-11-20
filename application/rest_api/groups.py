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
from application.common.date import get_calendar
from application.common.lessons import (
    DefaultLesson,
    create_new_passes,
    process_attended_lessons,
    process_not_attended_lessons,
    restore_database
)
from collections import defaultdict, namedtuple, Counter
from itertools import takewhile, chain


@auth
def get_list(request):
    u"""
    Функция для получения списка групп

    args:
        request django.http.request.HttpRequest

    return:
        django.http.response.HttpResponse
    """
    data = [
        g.__json__()
        for g in Groups.objects.all()
    ]

    return HttpResponse(json.dumps(data))


@auth
def get_base_info(request):
    u"""
    Функция для получения данных для одной группы
    args:
        request django.http.request.HttpRequest

    return:
        django.http.response.HttpResponse
    """

    #TODO Тут оставить только прием запроса и отправку ответа
    #TODO остальное вынести в common.group

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

        lessons_map[student].sort(key=lambda x: x.date)

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


@auth
def process_lesson(request):
    u"""
    Функция для обработки занятия в группе.
    Проставляет отметки о посещенных уроках, создает новые абонементы и
    уроки к ним, обрабатывает долги

    args:
        request django.http.request.HttpRequest

    return:
        django.http.response.HttpResponse

    """
    try:
        data = json.loads(request.body)
    except Exception:
        return HttpResponseServerError("Data is not valid")

    group = Groups.objects.get(pk=data['group'])
    date = datetime.strptime(data['date'], '%d.%m.%Y')

    attended = [
        s
        for s in data['students']
        if s['lesson']['status'] == Lessons.STATUSES['attended'] \
        and s['lesson']['is_new'] == False
    ]

    not_attended = [
        s
        for s in data['students']
        if s['lesson']['status'] == Lessons.STATUSES['not_attended'] \
        and s['lesson']['is_new'] == False
    ]

    new_passes = [
        s for s in data['students']
        if s['lesson']['is_new'] == True
    ]

    if len(new_passes) > 0:
        create_new_passes(group, date, new_passes)
        attended += new_passes

    if len(attended) > 0:
        process_attended_lessons(group, date, attended)

    if len(not_attended) > 0:
        process_not_attended_lessons(group, date, not_attended)

    if len(attended) + len(not_attended):
        restore_database(group, date, chain(attended, not_attended))

    return HttpResponse()

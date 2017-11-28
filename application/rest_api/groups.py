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
    get_students_lessons,
    restore_database,
    delete_lessons as delete_lessons_func,
    move_lessons as move_lessons_func
)
from application.common.group import get_students
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

    students = get_students(group).order_by('last_name', 'first_name')
    lessons = get_students_lessons(group, dates[0], dates[-1], students)

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
                    for l in lessons[student]
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

    only_id = [s['stid'] for s in new_passes]

    # TODO Наверное можно и по изящнее как-то
    dates = list(takewhile(
        lambda x: x.month == date.month,
        get_calendar(date.replace(day=1), group.days)
    ))

    date_from, date_to = dates[0::len(dates)-1]

    new_lessons = get_students_lessons(group, date_from, date_to, only_id)
    new_lessons_json = dict()
    for st, ls in new_lessons.iteritems():
        new_lessons_json[str(st)] = [l.__json__() for l in ls]

    return HttpResponse(json.dumps(new_lessons_json))


@auth
def delete_lessons(request):
    u"""
    Функция для удаления занятий у выбранного ученика
    args:
        request django.http.request.HttpRequest

    return:
        django.http.response.HttpResponse
    """
    try:
        data = json.loads(request.body)
        date = datetime.strptime(data['date'], "%d.%m.%Y")
        delete_lessons_func(date, data['count'], data['stid'], data['group'])

        lessons = get_students_lessons(
            data['group'],
            date.replace(day=1),
            None,
            [data['stid']]
        )

        lessons_json = [l.__json__() for l in lessons[data['stid']]]
        return HttpResponse(json.dumps(lessons_json))

    except Exception:
        return HttpResponseServerError(format_exc())


@auth
def move_lessons(request):
    u"""
    Функция для переноса занятий у выбранного ученика
    args:
        request django.http.request.HttpRequest

    return:
        django.http.response.HttpResponse
    """
    try:
        data = json.loads(request.body)
        date_from = datetime.strptime(data['date_from'], "%d.%m.%Y")
        date_to = datetime.strptime(data['date_to'], "%d.%m.%Y")

        move_lessons_func(date_from, date_to, data['stid'], data['group'])

        lessons = get_students_lessons(
            data['group'],
            date_from.replace(day=1),
            None,
            [data['stid']]
        )

        lessons_json = [l.__json__() for l in lessons[data['stid']]]
        return HttpResponse(json.dumps(lessons_json))

    except Exception:
        return HttpResponseServerError(format_exc())

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
from collections import defaultdict, namedtuple, Counter
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


@auth
def process_lesson(request):
    try:
        data = json.loads(request.body)
    except Exception:
        return HttpResponseServerError("Data is not valid")

    group = Groups.objects.get(pk=data['group'])
    date = datetime.strptime(data['date'], '%d.%m.%Y')

    attended = (
        s
        for s in data['students']
        if s['lesson']['status'] == Lessons.STATUSES['attended'] \
        and s['lesson']['is_new'] == False
    )

    Lessons.objects.filter(
        group=group,
        date=date,
        student_id__in=[s['stid'] for s in attended]
    ).update(status=Lessons.STATUSES['attended'])

    not_attended = (
        s
        for s in data['students']
        if s['lesson']['status'] == Lessons.STATUSES['not_attended'] \
        and s['lesson']['is_new'] == False
    )

    process_not_attended_lessons(group, date, not_attended)
    restore_database(group, date, attended, not_attended)

    new_passes = (
        s
        for s in data['students']
        if s['lesson']['is_new'] == True
    )

    return HttpResponse()


# Функция для отмечания пропусков и непосещенных занятий
def process_not_attended_lessons(group, date, lessons):
    # TODO Обработка пропуска
    #   1. ОРГ
    #   2. Кол-во пропусков < чем заявленное
    #   3. Кол-во пропусков > чем заявленное

    Data = namedtuple("LessonData", ['student', 'pid', 'skips', 'org'])
    data = [
        Data(*l)
        for l in Lessons.objects.filter(
            group=group,
            date=date,
            student_id__in=[s['stid'] for s in lessons]
        ) \
        .select_related() \
        .values_list(
            'student',
            'group_pass__id',
            'group_pass__skips_origin',
            'student__org'
        )
    ]

    missed_lessons = Counter(
        Lessons.objects.filter(
            group_pass_id__in=[l.pid for l in data],
            status=Lessons.STATUSES['moved'],
            date__lte=date
        ).values_list('student', flat=True)
    )

    not_attended = (
        s.student
        for s in data if not s.org and s.skips <= missed_lessons[s.student]
    )
    moved = (
        s.student
        for s in data if s.org or s.skips > missed_lessons[s.student]
    )

    Lessons.objects.filter(
        group=group,
        date=date,
        student_id__in=not_attended
    ).update(status=Lessons.STATUSES['not_attended'])

    Lessons.objects.filter(
        group=group,
        date=date,
        student_id__in=moved
    ).update(status=Lessons.STATUSES['moved'])


# Функция для провекри соответствия количества
# занятий в базе, указанному количеству абонементов
def restore_database(group, date, stdents):
    pass

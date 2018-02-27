#!/usr/bin/env python
# -*- coding: utf-8 -*-


import json
from auth import auth
from application.models import Comments

from django.http.response import (
    HttpResponse,
    HttpResponseServerError,
)
from traceback import format_exc
import datetime
from application.settings import TIME_ZONE
from pytz import timezone


@auth
def edit_comment(request):
    u"""
    Функция для обработки коментариев

    args:
        request django.http.request.HttpRequest

    return:
        django.http.response.HttpResponse
    """

    try:
        data = json.loads(request.body)
        date = datetime.datetime.now(timezone(TIME_ZONE))

        try:
            comment = Comments.objects.filter(
                group_id=data['group'],
                student_id=data['student']
            ).last()

            comment.text = data['text']
            comment.add_date = date

        except Comments.DoesNotExist:
            comment = Comments(
                group_id=data['group'],
                student_id=data['student'],
                add_date=date,
                text=data['text']
            )

        if not comment.text:
            if comment.id is not None:
                comment.delete()
        else:
            comment.save()

        response = dict(
            status="OK",
            time=date.strftime('%d.%m.%Y %H:%M')
        )

        return HttpResponse(json.dumps(response))

    except Exception:
        return HttpResponseServerError(format_exc())

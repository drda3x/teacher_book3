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
        date = datetime.datetime.now()
        comment, _ = Comments.objects.get_or_create(
            group_id=data['group'],
            student_id=data['student']
        )

        comment.text = data['text']
        comment.add_date = date

        if not comment.text:
            comment.delete()
        else:
            comment.save()

        return HttpResponse()

    except Exception:
        return HttpResponseServerError(format_exc())

#!/usr/bin/env python
# -*- coding: utf-8 -*-


from django.http.response import (
    HttpResponse,
    HttpResponseServerError,
)

from auth import auth


@auth
def get_sampo_day_info(request):
    u"""
    Функция для получения всей информации о сампо за день

    @request <django.HttpRequest>

    @return <django.HttpResponse>
    """

    print request.body
    return HttpResponse()

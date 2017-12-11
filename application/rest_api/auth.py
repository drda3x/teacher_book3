#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.contrib import auth as auth_origin
from django.http import HttpResponseForbidden, HttpResponse
from django.contrib.sessions.backends.db import SessionStore
from application.models import User
import json


def auth(request_processor):
    u"""
    Функция-декоратор для проверки авторизации и авторизации пользователей
    Создает обертку для исходного обработчика и перед его выполнением прове
    ряет авторизацию

    args:
        request_processor function

    return:
        function
    """

    def wrapper(request, *args, **kwargs):
        try:
            uid = request.session['uid']
            user = User.objects.get(pk=uid)
        except KeyError:
            user = None
        except User.DoesNotExist:
            return HttpResponseForbidden()

        if user and user.is_authenticated():
            request.user = user
            return request_processor(request, *args, **kwargs)

        else:
            try:
                data = json.loads(request.body)
                username = data.get('username')
                password = data.get('password')
                user = auth_origin.authenticate(username=username, password=password)
            except ValueError:
                user = None

            if user and user.is_active:
                if 'remember' in request.POST:
                    auth.login(request, user)

                request.session = SessionStore()
                request.session['uid'] = user.id
                request.user = user

                return request_processor(request, *args, **kwargs)

            else:
                return HttpResponseForbidden()

    return wrapper


@auth
def login(request):
    data = dict(first_name=request.user.first_name, last_name=request.user.last_name)
    return HttpResponse(json.dumps(data))


def logout(request):
    request.session.delete()
    auth_origin.logout(request)
    return HttpResponse()

#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.contrib import auth as auth_origin
from django.http import HttpResponseForbidden, HttpResponse
from django.contrib.sessions.backends.db import SessionStore
from application.models import User
import json


# Декоратор для проверки авторизации
def auth(request_processor):
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
    return HttpResponse()

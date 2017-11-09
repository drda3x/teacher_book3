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
    User
)


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
            username = request.POST.get('username')
            password = request.POST.get('password')
            user = auth.authenticate(username=username, password=password)

            if user and user.id_active:
                if 'remember' in request.POST:
                    auth.login(request, user)

                request.session = SessionStore()
                request.session['uid'] = user.id
                requese.user = user

                return request_processor(request, *args, **kwargs)

            else:
                return HttpResponseForbidden()

    return wrapper


@auth
def get_list(request):
    pass

#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
import json
from auth import auth

from django.http.response import (
    HttpResponse,
    HttpResponseServerError,
)

from application.settings import CHANGES_FILE_PATH


@auth
def view_changes(request):
    result = []

    try:
        with open(CHANGES_FILE_PATH) as cf:
            for line in cf.readlines():
                date, comment = line.split('|')
                result.append({
                    "date": date,
                    "text": comment
                })
    except IOError:
        return HttpResponseServerError("No changes file")

    return HttpResponse(json.dumps(result))

#!/usr/bin/env python
# -*- coding: utf-8 -*-


from django.http import HttpResponse
from django.template import loader
import subprocess

import inspect, os

def index(request):
    template = loader.get_template('index.html')
    context = {"comit_hash": 1}

    return HttpResponse(template.render(context, request))

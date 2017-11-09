#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.http import HttpResponse
from django.template import loader


def page1(request):
    template = loader.get_template('page1.html')
    context = {}

    return HttpResponse(template.render(context, request))

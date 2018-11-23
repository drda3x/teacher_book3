#!/usr/bin/env python
# -*- coding: utf-8 -*-


from django.http.response import (
    HttpResponse,
    HttpResponseServerError,
)

import application.models as models
import json
import datetime

from auth import auth


@auth
def get_sampo_day_info(request):
    u"""
    Функция для получения всей информации о сампо за день

    @param request {django.HttpRequest}

    @return {django.HttpResponse|django.HttpResponseServerError}
    """

    try:
        data = json.loads(request.body)
        date_b = datetime.datetime.strptime(data['date'], '%d.%m.%Y')
        date_e = datetime.datetime.strptime('%s 23:59:59' % data['date'],
                                            '%d.%m.%Y %H:%M:%S')
        day_payments = models.SampoPayments.objects.filter(
            date__range=(date_b, date_e),
            hall_id=data['hall']
        )

        fdm = date_b.replace(day=1)
        edm = fdm + datetime.timedelta(days=35)
        edm = edm.replace(day=1)
        passes = models.SampoPasses.objects.select_related().filter(
            payment__in=models.SampoPayments.objects.filter(date__gte=fdm,
                                             date__lt=edm)
        ).order_by('surname', 'name')
        usages = models.SampoPassUsage.objects.select_related().filter(
            sampo_pass__in=passes,
            date__range=(date_b, date_e)
        ).values_list('sampo_pass_id', flat=True)

        responce = dict()
        responce['payments'] = [
            (
                payment.date.strftime('%d.%m.%Y %H:%M:%S'),
                payment.money,
                payment.comment
            )
            for payment in list(day_payments)
        ]
        responce['passes'] = [
            (
                "%s %s" % (p.surname, p.name),
                p.id in usages
            )
            for p in passes
        ]

        return HttpResponse(json.dumps(responce))

    except Exception:
        from traceback import format_exc
        print format_exc()

        return HttpResponseServerError(format_exc())

@auth
def add_sampo_payment(request):
    u"""
    Добавить запись об оплате

    @param request {django.HttpRequest}

    @return {django.HttpResponse|django.HttpResponseServerError}
    """

    try:
        data = json.loads(request.body)
        date = datetime.datetime.strptime(
            "%s %s" % (data['date'], data['time']),
            "%d.%m.%Y %H:%M"
        )
        payment = models.SampoPayments(
            date=date,
            money=data['amount'],
            hall_id=data['hall'],
            staff=request.user,
            people_count=0
        )
        payment.save()

        return HttpResponse()

    except Exception:
        from traceback import format_exc
        print format_exc()

        return HttpResponseServerError(format_exc())


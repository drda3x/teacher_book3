#!/usr/bin/env python
# -*- coding: utf-8 -*-


from django.http.response import (
    HttpResponse,
    HttpResponseServerError,
)

import application.models as models
from django.db.models import Sum
import json
import datetime
import itertools
import collections

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
def get_sampo_month_info(request):
    u"""
    Получить информацию о сампо за месяц

    :request {django.HttpRequest}
    :response {django.HttpResponse | django.HttpResponseServerError}
    """
    try:

        day_end = datetime.datetime.now().replace(hour=23, minute=59, second=59, microsecond=0)
        day_begin = datetime.datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        prev_balance = dict(models.SampoPayments.objects.select_related() \
        .filter(date__lt=day_begin).values_list('hall_id').annotate(total=Sum('money')))
        payments = models.SampoPayments.objects.select_related().filter(date__range=[day_begin, day_end]).order_by("date", "hall")
        passes = models.SampoPasses.objects.filter(payment__in=payments).values_list("payment_id", flat=True)

        _payments = (
            dict(amount=p.money,
                date=p.date.strftime('%d'),
                id=p.id,
                hall=p.hall.id,
                comment=p.comment)
            for p in payments
        )

        result = []
        for k, v in itertools.groupby(_payments, lambda x: (x['date'], x['hall'])):
            total, s_passes, withdrawals = 0, 0, 0
            dt, hall = k
            l_withdrawals = []

            for val in v:
                if val['amount']> 0:
                    total += val['amount']
                else:
                    withdrawals += abs(val['amount'])
                    l_withdrawals.append(val)

                if val['id'] in passes:
                    s_passes += val['amount']

            prev_balance[hall] = prev_balance.get(hall, 0) + total - withdrawals

            result.append(dict(date=dt,
                               prev_day_balance=prev_balance[hall],
                               hall=hall,
                               total=total,
                               passes=s_passes,
                               withdrawals=withdrawals,
                               l_withdrawals=l_withdrawals))



        return HttpResponse(json.dumps(result))

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
            comment=data.get('comment', ''),
            staff=request.user,
            people_count=0
        )
        payment.save()

        return HttpResponse()

    except Exception:
        from traceback import format_exc
        print format_exc()

        return HttpResponseServerError(format_exc())

@auth
def add_sampo_pass(request):
    u"""
    Добавить запись сампо

    :param request {django.HttpRequest}
    :return {django.HttpResponse|django.HttpResponseServerError}
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
            comment=data.get('comment', ''),
            staff=request.user,
            people_count=0
        )
        payment.save()

        surname, name = data['name'].split()
        sampo_pass = models.SampoPasses(
            payment=payment,
            surname=surname,
            name=name
        )
        sampo_pass.save()

        pass_usage = models.SampoPassUsage(
            sampo_pass=sampo_pass,
            date=date,
            hall_id=data['hall']
        )
        pass_usage.save()

        return HttpResponse()

    except Exception:
        from traceback import format_exc
        print format_exc()

        return HttpResponseServerError(format_exc())

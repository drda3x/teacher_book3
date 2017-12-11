#!/usr/bin/env python
# -*- coding: utf-8 -*-


import datetime

WEEK = (
    (0, u'Пн'),
    (1, u'Вт'),
    (2, u'Ср'),
    (3, u'Чт'),
    (4, u'Пт'),
    (5, u'Сб'),
    (6, u'Вс')
)

MONTH_RUS = [
    '',
    u'Январь',
    u'Февраль',
    u'Март',
    u'Апрель',
    u'Май',
    u'Июнь',
    u'Июль',
    u'Август',
    u'Сентябрь',
    u'Октябрь',
    u'Ноябрь',
    u'Декабрь'
]

MONTH_PARENT_FORM = [
    '',
    u'Января',
    u'Февраля',
    u'Марта',
    u'Апреля',
    u'Мая',
    u'Июня',
    u'Июля',
    u'Августа',
    u'Сентября',
    u'Октября',
    u'Ноября',
    u'Декабря'
]


def get_calendar(date, week_days, direction="forward"):
    u"""
    Функция для генерации последовательности
    дат из определенных дней недели

        args:
            date datetime.datetime
            week_days [int]

        yield:
            datetime.datetime
    """

    wdn = [d[0] for d in WEEK if d[1] in week_days]
    _date = date + datetime.timedelta(days=0)

    while True:
        if _date.weekday() in wdn:
            yield _date

        if direction == "forward":
           _date += datetime.timedelta(days=1)

        elif direction == "backward":
           _date -= datetime.timedelta(days=1)

        else:
             raise Exception("wrong direction walue")

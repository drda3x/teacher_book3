#!/usr/bin/env python
# -*- coding: utf-8 -*-


from collections import namedtuple
from date import get_calendar
from itertools import takewhile


class DefaultLesson(namedtuple("DefaultLesson", ["date", "status"])):

    def __json__(self):
        return dict(
            date=self.date.strftime("%d.%m.%Y"),
            status=self.status
        )


def get_students_lessons(group, date, students):

    dates = takewhile(
        lambda x: x.month==date.month,
        get_calendar(date, group.days)
    )

    return (DefaultLesson(date, -2) for date in dates)

#!/usr/bin/env python
# -*- coding: utf-8 -*-


from collections import namedtuple
from date import get_calendar
from itertools import takewhile


class DefaultLesson(namedtuple("DefaultLesson", ["date", "status"])):
    u"""
        Структура для сохранения интерфейса класса
        application.models.Lessons
    """

    def __json__(self):
        return dict(
            date=self.date.strftime("%d.%m.%Y"),
            status=self.status
        )


# Структура для объединения
# application.models.Students и application.models.PassTypes
PassTypeStudent = namedtuple("PassTypeStudent", ["student", "pass_type"])


def get_students_lessons(group, date, students):
    u"""
        Функция для получения списка уроков для заданного
        списка учеников

        args:
            group application.models.Groups
            date datetime.datetime
            students [application.models.Students]

        return:
            [application.models.Lessons or DefaultLesson]
    """

    dates = takewhile(
        lambda x: x.month == date.month,
        get_calendar(date, group.days)
    )

    return (DefaultLesson(date, -2) for date in dates)


def create_new_passes(group, date, pt_data):
    u"""
        Функция для создания и сохранения абонементов в БД

        args:
            group application.models.Groups
            data datetime.datetime
            pd_data PassTypeStudent
    """
    pass

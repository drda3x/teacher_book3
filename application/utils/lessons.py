#!/usr/bin/env python
# -*- coding: utf-8 -*-


from collections import namedtuple


class DefaultLesson(namedtuple("DefaultLesson", ["date", "status"])):

    def __json__(self):
        return dict(
            date=self.date.strftime("%d.%m.%Y"),
            status=self.status
        )

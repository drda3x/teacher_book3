#!/usr/bin/env python
# -*- coding: utf-8 -*-

from application import models as app_models
from django.db.models import Model as django_models_class


def get_models(fk_class):
    u'''
    Получить список моделей у которых есть оперделенный ForeinKey
    :param fk_class: models.Model
    :return: list
    '''

    result = []  # список кортежей типа: ("имя поля", "класс модели")

    objects = (getattr(app_models, name) for name in dir(app_models))
    models = (
        obj for obj in objects
        if obj.__class__ == django_models_class.__class__ and obj != fk_class
    )

    for model in models:
        fields = []

        for field_name in dir(model):
            try:
                fields.append( (field_name, getattr(model, field_name)) )
            except AttributeError:
                continue

        #fields = map(lambda name: (name, getattr(model, name)), dir(model))
        for field in fields:
            try:
                name, obj = field[0:2]
                if obj.field.related and obj.field.related_model == fk_class:
                    result.append((name, model))

            except Exception:
                pass

    return result

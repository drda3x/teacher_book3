#!/usr/bin/env python
# -*- coding: utf-8 -*-


from application.models import Students
from application.utils.system import get_models
from django.core.exceptions import MultipleObjectsReturned
from phones import check_phone


def edit_student(stid, phone, first_name, last_name, org_status):
    u"""
    Функция для создания/изменения учеников в системе

    args:
        stid int
        phone str
        first_name str
        last_name str
        org_status bool

    return:
        application.models.Students
    """
    phone = check_phone(phone)
    first_name = first_name.replace(' ', '')
    last_name = last_name.replace(' ', '')

    try:
        if stid is not None:
            student = Students.objects.get(
                pk=stid
            )
        else:
            student = Students.objects.get(
                first_name=first_name,
                last_name=last_name,
                phone=phone
            )

    except MultipleObjectsReturned:
        student = Students.objects.filter(
            first_name=first_name,
            last_name=last_name,
            phone=phone
        ).first()

        check_duplications(student.id, phone, name, last_name, org_status)

    except Students.DoesNotExist:
        student = Students(
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            org=org_status
        )

        student.save()

    student.first_name = first_name
    student.last_name = last_name
    student.phone = phone
    student.org = org_status
    student.save()

    return student


def check_duplicates(stid, phone, name, last_name, org_status):
    u"""
    Функция для проверки наличия и удаления дубликатов записей
    учеников в системе

    args:
        stid int
        phone str
        name str
        last_name str
        org_status bool
    """
    phone = check_phone(phone)
    first_name = first_name.replace(' ', '')
    last_name = last_name.replace(' ', '')

    if not phone:
        raise TypeError('Phone must be a number')

    # Проверить наличие такого же тлефона
    try:
        def check_names(human):
            same_fn = human.first_name.lower() == first_name.lower()
            same_ln = human.last_name.lower() == last_name.lower()
            return same_fn and same_ln

        same_phone_people = Students.objects \
            .filter(phone=phone) \
            .exclude(pk=stid)

        change_list = filter(check_names, same_phone_people)

        # В списке на изменение что-то есть - проходим по всем моделям
        # у которых есть ForeinKey на Students и
        # меняем записи для собранного change_list'a
        if change_list:
            models = get_models(Students)

            for human in change_list:
                human_backup = deepcopy(human)

                # список для сохранения предыдущих состояний базы.
                back_up = []

                try:
                    for model in models:
                        cls = model[1]
                        field_name = model[0]
                        params = {field_name: human}
                        records = cls.objects.filter(**params)

                        for record in records:
                            back_up.append(deepcopy(record))
                            setattr(record, field_name, student)
                            record.save()

                    human.delete()

                except Exception:
                    # Если одно из сохранений провалилось - восстанавливаем предыдущее состояние
                    # для всех записей конкретного человека
                    for record in back_up:
                        record.save()

                    human_backup.save()

        # В списке людей с одинаковыми именами и телефонами что-то есть.
        # выдаем информацию об этимх записях
        if errors:
            pass

    # Совпадений нет
    except Students.DoesNotExist:
        pass

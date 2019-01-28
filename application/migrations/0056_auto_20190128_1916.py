# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('application', '0055_groups_dance_halls'),
    ]

    operations = [
        migrations.AlterField(
            model_name='groups',
            name='dance_hall',
            field=models.ForeignKey(verbose_name='\u0417\u0430\u043b', blank=True, to='application.DanceHalls', null=True),
        ),
        migrations.AlterField(
            model_name='groups',
            name='dance_halls',
            field=models.ManyToManyField(related_name='dance_halls', null=True, verbose_name='\u0417\u0430\u043b\u044b', to='application.DanceHalls', blank=True),
        ),
    ]

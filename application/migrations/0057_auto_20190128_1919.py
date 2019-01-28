# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('application', '0056_auto_20190128_1916'),
    ]

    operations = [
        migrations.AddField(
            model_name='lessons',
            name='dance_hall',
            field=models.ForeignKey(verbose_name='\u0417\u0430\u043b', blank=True, to='application.DanceHalls', null=True),
        ),
        migrations.AlterField(
            model_name='groups',
            name='dance_hall',
            field=models.ForeignKey(verbose_name='\u0417\u0430\u043b \u043f\u043e \u0443\u043c\u043e\u043b\u0447\u0430\u043d\u0438\u044e', blank=True, to='application.DanceHalls', null=True),
        ),
    ]

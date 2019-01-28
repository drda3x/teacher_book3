# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('application', '0054_auto_20181121_0608'),
    ]

    operations = [
        migrations.AddField(
            model_name='groups',
            name='dance_halls',
            field=models.ManyToManyField(related_name='dance_halls', verbose_name='\u0417\u0430\u043b\u044b', to='application.DanceHalls'),
        ),
    ]

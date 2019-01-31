# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('application', '0058_dancehalltolesson'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dancehalltolesson',
            name='dance_hall',
            field=models.ForeignKey(verbose_name='Dance Hall', blank=True, to='application.DanceHalls', null=True),
        ),
    ]

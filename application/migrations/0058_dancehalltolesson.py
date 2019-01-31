# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('application', '0057_auto_20190128_1919'),
    ]

    operations = [
        migrations.CreateModel(
            name='DanceHallToLesson',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateField(verbose_name='\u0414\u0430\u0442\u0430')),
                ('dance_hall', models.ForeignKey(verbose_name='Dance Hall', to='application.DanceHalls')),
                ('group', models.ForeignKey(verbose_name='Group', to='application.Groups')),
            ],
        ),
    ]

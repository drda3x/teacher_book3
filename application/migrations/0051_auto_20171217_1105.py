# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('application', '0050_auto_20171129_1509'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comments',
            name='add_date',
            field=models.DateTimeField(null=True, verbose_name='\u0414\u0430\u0442\u0430 \u0434\u043e\u0431\u0430\u0432\u043b\u0435\u043d\u0438\u044f', blank=True),
        ),
    ]

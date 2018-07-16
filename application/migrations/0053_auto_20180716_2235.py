# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('application', '0052_grouplevels_sort_num'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='lessons',
            unique_together=set([('date', 'student', 'group')]),
        ),
    ]

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('application', '0055_auto_20181102_0744'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='sampopayments',
            name='hall',
        ),
    ]

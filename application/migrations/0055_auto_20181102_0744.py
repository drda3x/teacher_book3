# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('application', '0054_auto_20181102_0557'),
    ]

    operations = [
        migrations.RenameField(
            model_name='sampopassusage',
            old_name='dance_hall',
            new_name='hall',
        ),
        migrations.RenameField(
            model_name='sampopayments',
            old_name='dance_hall',
            new_name='hall',
        ),
    ]

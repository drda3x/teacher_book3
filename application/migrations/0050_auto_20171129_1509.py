# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('application', '0049_administratorlist_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dancehalls',
            name='map',
            field=models.FileField(null=True, upload_to=b'/', blank=True),
        ),
        migrations.AlterField(
            model_name='dancehalls',
            name='photo1',
            field=models.FileField(null=True, upload_to=b'/', blank=True),
        ),
        migrations.AlterField(
            model_name='dancehalls',
            name='photo2',
            field=models.FileField(null=True, upload_to=b'/', blank=True),
        ),
        migrations.AlterField(
            model_name='dancehalls',
            name='photo3',
            field=models.FileField(null=True, upload_to=b'/', blank=True),
        ),
        migrations.AlterField(
            model_name='lessons',
            name='status',
            field=models.IntegerField(default=0, verbose_name='\u0421\u0442\u0430\u0442\u0443\u0441 \u0437\u0430\u043d\u044f\u0442\u0438\u044f', choices=[(2, b'not_attended'), (1, b'attended'), (3, b'frozen'), (5, b'written_off'), (4, b'moved'), (0, b'not_processed'), (6, b'canceled')]),
        ),
        migrations.AlterField(
            model_name='user',
            name='photo',
            field=models.FileField(upload_to=b'/', null=True, verbose_name='\u0424\u043e\u0442\u043e', blank=True),
        ),
    ]

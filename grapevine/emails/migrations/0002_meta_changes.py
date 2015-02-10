# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('emails', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='email',
            name='from_email',
            field=models.CharField(default='ClanHall <no-reply@clanhall.co>', max_length=255, db_index=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='email',
            name='reply_to',
            field=models.EmailField(default='no-reply@clanhall.co', max_length=255, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='email',
            name='subject',
            field=models.CharField(default='Hello from ClanHall!', max_length=255),
            preserve_default=True,
        ),
    ]

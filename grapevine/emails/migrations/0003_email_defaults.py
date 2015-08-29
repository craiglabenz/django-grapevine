# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('emails', '0002_meta_changes'),
    ]

    operations = [
        migrations.AlterField(
            model_name='email',
            name='from_email',
            field=models.CharField(default='', max_length=255, db_index=True),
        ),
        migrations.AlterField(
            model_name='email',
            name='reply_to',
            field=models.EmailField(default='', max_length=255, blank=True),
        ),
        migrations.AlterField(
            model_name='email',
            name='subject',
            field=models.CharField(default='', max_length=255),
        ),
    ]

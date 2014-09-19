# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='QueuedMessage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('message_id', models.PositiveIntegerField(verbose_name='Message Id')),
                ('message_type', models.ForeignKey(verbose_name='Message Type', to='contenttypes.ContentType')),
            ],
            options={
                'verbose_name': 'Queued Message',
                'verbose_name_plural': 'Queued Messages',
            },
            bases=(models.Model,),
        ),
    ]

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Email',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('html_body', models.TextField(blank=True)),
                ('text_body', models.TextField(blank=True)),
                ('status', models.IntegerField(default=2, db_index=True, choices=[(1, 'Sent'), (3, 'Failed'), (2, 'Unsent'), (4, 'Send-time Error'), (5, 'Newsletter'), (6, 'Duplicate'), (7, 'Unsubscribed')])),
                ('sent_at', models.DateTimeField(default=None, null=True, verbose_name='Sent At', db_index=True, blank=True)),
                ('communication_time', models.DecimalField(decimal_places=5, default=None, max_digits=8, blank=True, help_text='In seconds', null=True, verbose_name='Communication Time')),
                ('is_test', models.BooleanField(default=False, db_index=True, verbose_name='Is Test')),
                ('guid', models.CharField(db_index=True, max_length=36, null=True, blank=True)),
                ('log', models.TextField(default=None, null=True, blank=True)),
                ('from_email', models.CharField(default='Craig Labenz <admins@djangograpevine.com>', max_length=255, db_index=True)),
                ('reply_to', models.EmailField(default='help@djangograpevine.com', max_length=255, blank=True)),
                ('subject', models.CharField(default='Hello from Grapevine!', max_length=255)),
            ],
            options={
                'verbose_name': 'Email',
                'verbose_name_plural': 'Emails',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='EmailBackend',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=255)),
                ('path', models.CharField(help_text='The dotted import path to this backend, in a structure that would satisfy settings.EMAIL_BACKEND.', max_length=255)),
                ('username', models.CharField(help_text='Depending on the provider, this may actually be an API key.', max_length=255, blank=True)),
                ('password', models.CharField(help_text='Depending on the provider, this may actually be an API secret.', max_length=255, blank=True)),
            ],
            options={
                'verbose_name': 'Email Backend',
                'verbose_name_plural': 'Email Backends',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='EmailEvent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('happened_at', models.DateTimeField(verbose_name='Happened At', db_index=True)),
                ('email', models.ForeignKey(related_name='events', to='emails.Email')),
            ],
            options={
                'verbose_name': 'Email Event',
                'verbose_name_plural': 'Email Events',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='EmailRecipient',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('address', models.EmailField(max_length=254, verbose_name='Recipient Address', db_index=True)),
                ('domain', models.CharField(max_length=100, db_index=True)),
                ('name', models.CharField(max_length=150, blank=True)),
                ('type', models.IntegerField(default=1, choices=[(1, 'To'), (2, 'CC'), (3, 'BCC')])),
                ('email', models.ForeignKey(related_name='recipients', to='emails.Email')),
            ],
            options={
                'verbose_name': 'Email Recipient',
                'verbose_name_plural': 'Email Recipients',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='EmailVariable',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('key', models.CharField(max_length=100)),
                ('value', models.CharField(help_text='1 represents True, and 0 represents False.', max_length=5000, blank=True)),
                ('email', models.ForeignKey(related_name='variables', to='emails.Email')),
            ],
            options={
                'verbose_name': 'Email Variable',
                'verbose_name_plural': 'Email Variables',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=100)),
                ('should_stop_sending', models.BooleanField(default=False, verbose_name='Should Stop Sending')),
            ],
            options={
                'verbose_name': 'Event',
                'verbose_name_plural': 'Events',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='RawEvent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('payload', models.TextField()),
                ('processed_on', models.DateTimeField(default=None, null=True, verbose_name='Processed On', blank=True)),
                ('processed_in', models.DecimalField(decimal_places=4, default=None, max_digits=5, blank=True, null=True, verbose_name='Processed In')),
                ('is_queued', models.BooleanField(default=False, db_index=True, verbose_name='Is Queued')),
                ('is_broken', models.NullBooleanField(default=None, verbose_name='Is Broken', db_index=True)),
                ('remote_ip', models.GenericIPAddressField(verbose_name='Remote IP', db_index=True)),
                ('backend', models.ForeignKey(to='emails.EmailBackend')),
            ],
            options={
                'verbose_name': 'Raw Event',
                'verbose_name_plural': 'Raw Events',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UnsubscribedAddress',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('address', models.CharField(max_length=255, db_index=True)),
                ('email', models.ForeignKey(related_name='unsubscribed_addresses', default=None, blank=True, to='emails.Email', help_text='Optional link back to the Email in which this recipient address         clicked Unsubscribe.', null=True)),
            ],
            options={
                'verbose_name': 'Unsubscribed Address',
                'verbose_name_plural': 'Unsubscribed Addresses',
            },
            bases=(models.Model,),
        ),
        migrations.AlterIndexTogether(
            name='emailvariable',
            index_together=set([('key', 'value')]),
        ),
        migrations.AddField(
            model_name='emailevent',
            name='event',
            field=models.ForeignKey(related_name='email_events', to='emails.Event'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='emailevent',
            name='raw_event',
            field=models.ForeignKey(related_name='email_events', verbose_name='Raw Event', to='emails.RawEvent'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='email',
            name='backend',
            field=models.ForeignKey(to='emails.EmailBackend', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='email',
            name='type',
            field=models.ForeignKey(default=None, blank=True, to='contenttypes.ContentType', null=True),
            preserve_default=True,
        ),
    ]

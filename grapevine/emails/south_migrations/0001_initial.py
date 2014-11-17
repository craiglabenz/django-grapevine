# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Email'
        db.create_table(u'emails_email', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('type', self.gf('django.db.models.fields.related.ForeignKey')(default=None, to=orm['contenttypes.ContentType'], null=True, blank=True)),
            ('html_body', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('text_body', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('status', self.gf('django.db.models.fields.IntegerField')(default=2, db_index=True)),
            ('sent_at', self.gf('django.db.models.fields.DateTimeField')(default=None, null=True, db_index=True, blank=True)),
            ('communication_time', self.gf('django.db.models.fields.DecimalField')(default=None, null=True, max_digits=8, decimal_places=5, blank=True)),
            ('is_test', self.gf('django.db.models.fields.BooleanField')(default=False, db_index=True)),
            ('guid', self.gf('django.db.models.fields.CharField')(db_index=True, max_length=36, null=True, blank=True)),
            ('log', self.gf('django.db.models.fields.TextField')(default=None, null=True, blank=True)),
            ('backend', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['emails.EmailBackend'], blank=True)),
            ('from_email', self.gf('django.db.models.fields.CharField')(default=u'Craig Labenz <admins@djangograpevine.com>', max_length=255, db_index=True)),
            ('reply_to', self.gf('django.db.models.fields.EmailField')(default=u'help@djangograpevine.com', max_length=255, blank=True)),
            ('subject', self.gf('django.db.models.fields.CharField')(default=u'Hello from Grapevine!', max_length=255)),
        ))
        db.send_create_signal(u'emails', ['Email'])

        # Adding model 'EmailRecipient'
        db.create_table(u'emails_emailrecipient', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('email', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'recipients', to=orm['emails.Email'])),
            ('address', self.gf('django.db.models.fields.EmailField')(max_length=254, db_index=True)),
            ('domain', self.gf('django.db.models.fields.CharField')(max_length=100, db_index=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=150, blank=True)),
            ('type', self.gf('django.db.models.fields.IntegerField')(default=1)),
        ))
        db.send_create_signal(u'emails', ['EmailRecipient'])

        # Adding model 'EmailBackend'
        db.create_table(u'emails_emailbackend', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('path', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('username', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('password', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
        ))
        db.send_create_signal(u'emails', ['EmailBackend'])

        # Adding model 'EmailVariable'
        db.create_table(u'emails_emailvariable', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('email', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'variables', to=orm['emails.Email'])),
            ('key', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=5000, blank=True)),
        ))
        db.send_create_signal(u'emails', ['EmailVariable'])

        # Adding index on 'EmailVariable', fields ['key', 'value']
        db.create_index(u'emails_emailvariable', ['key', 'value'])

        # Adding model 'RawEvent'
        db.create_table(u'emails_rawevent', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('backend', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['emails.EmailBackend'])),
            ('payload', self.gf('django.db.models.fields.TextField')()),
            ('processed_on', self.gf('django.db.models.fields.DateTimeField')(default=None, null=True, blank=True)),
            ('processed_in', self.gf('django.db.models.fields.DecimalField')(default=None, null=True, max_digits=5, decimal_places=4, blank=True)),
            ('is_queued', self.gf('django.db.models.fields.BooleanField')(default=False, db_index=True)),
            ('is_broken', self.gf('django.db.models.fields.NullBooleanField')(default=None, null=True, db_index=True, blank=True)),
            ('remote_ip', self.gf('django.db.models.fields.GenericIPAddressField')(max_length=39, db_index=True)),
        ))
        db.send_create_signal(u'emails', ['RawEvent'])

        # Adding model 'Event'
        db.create_table(u'emails_event', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('should_stop_sending', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'emails', ['Event'])

        # Adding model 'EmailEvent'
        db.create_table(u'emails_emailevent', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('email', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'events', to=orm['emails.Email'])),
            ('event', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'email_events', to=orm['emails.Event'])),
            ('raw_event', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'email_events', to=orm['emails.RawEvent'])),
            ('happened_at', self.gf('django.db.models.fields.DateTimeField')(db_index=True)),
        ))
        db.send_create_signal(u'emails', ['EmailEvent'])

        # Adding model 'UnsubscribedAddress'
        db.create_table(u'emails_unsubscribedaddress', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('address', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
            ('email', self.gf('django.db.models.fields.related.ForeignKey')(default=None, related_name=u'unsubscribed_addresses', null=True, blank=True, to=orm['emails.Email'])),
        ))
        db.send_create_signal(u'emails', ['UnsubscribedAddress'])


    def backwards(self, orm):
        # Removing index on 'EmailVariable', fields ['key', 'value']
        db.delete_index(u'emails_emailvariable', ['key', 'value'])

        # Deleting model 'Email'
        db.delete_table(u'emails_email')

        # Deleting model 'EmailRecipient'
        db.delete_table(u'emails_emailrecipient')

        # Deleting model 'EmailBackend'
        db.delete_table(u'emails_emailbackend')

        # Deleting model 'EmailVariable'
        db.delete_table(u'emails_emailvariable')

        # Deleting model 'RawEvent'
        db.delete_table(u'emails_rawevent')

        # Deleting model 'Event'
        db.delete_table(u'emails_event')

        # Deleting model 'EmailEvent'
        db.delete_table(u'emails_emailevent')

        # Deleting model 'UnsubscribedAddress'
        db.delete_table(u'emails_unsubscribedaddress')


    models = {
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'emails.email': {
            'Meta': {'object_name': 'Email'},
            'backend': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['emails.EmailBackend']", 'blank': 'True'}),
            'communication_time': ('django.db.models.fields.DecimalField', [], {'default': 'None', 'null': 'True', 'max_digits': '8', 'decimal_places': '5', 'blank': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'from_email': ('django.db.models.fields.CharField', [], {'default': "u'Craig Labenz <admins@djangograpevine.com>'", 'max_length': '255', 'db_index': 'True'}),
            'guid': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '36', 'null': 'True', 'blank': 'True'}),
            'html_body': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_test': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'log': ('django.db.models.fields.TextField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'reply_to': ('django.db.models.fields.EmailField', [], {'default': "u'help@djangograpevine.com'", 'max_length': '255', 'blank': 'True'}),
            'sent_at': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'db_index': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '2', 'db_index': 'True'}),
            'subject': ('django.db.models.fields.CharField', [], {'default': "u'Hello from Grapevine!'", 'max_length': '255'}),
            'text_body': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': u"orm['contenttypes.ContentType']", 'null': 'True', 'blank': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'emails.emailbackend': {
            'Meta': {'object_name': 'EmailBackend'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'path': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        u'emails.emailevent': {
            'Meta': {'object_name': 'EmailEvent'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'events'", 'to': u"orm['emails.Email']"}),
            'event': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'email_events'", 'to': u"orm['emails.Event']"}),
            'happened_at': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'raw_event': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'email_events'", 'to': u"orm['emails.RawEvent']"}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'emails.emailrecipient': {
            'Meta': {'object_name': 'EmailRecipient'},
            'address': ('django.db.models.fields.EmailField', [], {'max_length': '254', 'db_index': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'domain': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True'}),
            'email': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'recipients'", 'to': u"orm['emails.Email']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '150', 'blank': 'True'}),
            'type': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'emails.emailvariable': {
            'Meta': {'object_name': 'EmailVariable', 'index_together': "((u'key', u'value'),)"},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'variables'", 'to': u"orm['emails.Email']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '5000', 'blank': 'True'})
        },
        u'emails.event': {
            'Meta': {'object_name': 'Event'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'should_stop_sending': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'emails.rawevent': {
            'Meta': {'object_name': 'RawEvent'},
            'backend': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['emails.EmailBackend']"}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_broken': ('django.db.models.fields.NullBooleanField', [], {'default': 'None', 'null': 'True', 'db_index': 'True', 'blank': 'True'}),
            'is_queued': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'payload': ('django.db.models.fields.TextField', [], {}),
            'processed_in': ('django.db.models.fields.DecimalField', [], {'default': 'None', 'null': 'True', 'max_digits': '5', 'decimal_places': '4', 'blank': 'True'}),
            'processed_on': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'remote_ip': ('django.db.models.fields.GenericIPAddressField', [], {'max_length': '39', 'db_index': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'emails.unsubscribedaddress': {
            'Meta': {'object_name': 'UnsubscribedAddress'},
            'address': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "u'unsubscribed_addresses'", 'null': 'True', 'blank': 'True', 'to': u"orm['emails.Email']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['emails']
# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'HipChat'
        db.create_table(u'hipchat_hipchat', (
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
            ('room_id', self.gf('django.db.models.fields.IntegerField')(default=497734)),
            ('color', self.gf('django.db.models.fields.CharField')(default=u'yellow', max_length=50)),
            ('message_format', self.gf('django.db.models.fields.CharField')(default=u'html', max_length=50)),
            ('from_name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('should_notify', self.gf('django.db.models.fields.IntegerField')(default=1)),
        ))
        db.send_create_signal(u'hipchat', ['HipChat'])


    def backwards(self, orm):
        # Deleting model 'HipChat'
        db.delete_table(u'hipchat_hipchat')


    models = {
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'hipchat.hipchat': {
            'Meta': {'object_name': 'HipChat'},
            'color': ('django.db.models.fields.CharField', [], {'default': "u'yellow'", 'max_length': '50'}),
            'communication_time': ('django.db.models.fields.DecimalField', [], {'default': 'None', 'null': 'True', 'max_digits': '8', 'decimal_places': '5', 'blank': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'from_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'guid': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '36', 'null': 'True', 'blank': 'True'}),
            'html_body': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_test': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'log': ('django.db.models.fields.TextField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'message_format': ('django.db.models.fields.CharField', [], {'default': "u'html'", 'max_length': '50'}),
            'room_id': ('django.db.models.fields.IntegerField', [], {'default': '497734'}),
            'sent_at': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'db_index': 'True', 'blank': 'True'}),
            'should_notify': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '2', 'db_index': 'True'}),
            'text_body': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': u"orm['contenttypes.ContentType']", 'null': 'True', 'blank': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['hipchat']
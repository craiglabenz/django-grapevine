# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'HipChat.room_id'
        db.delete_column(u'hipchat_hipchat', 'room_id')

        # Adding field 'HipChat.to'
        db.add_column(u'hipchat_hipchat', 'to',
                      self.gf('django.db.models.fields.IntegerField')(default=497734),
                      keep_default=False)


    def backwards(self, orm):
        # Adding field 'HipChat.room_id'
        db.add_column(u'hipchat_hipchat', 'room_id',
                      self.gf('django.db.models.fields.IntegerField')(default=497734),
                      keep_default=False)

        # Deleting field 'HipChat.to'
        db.delete_column(u'hipchat_hipchat', 'to')


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
            'sent_at': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'db_index': 'True', 'blank': 'True'}),
            'should_notify': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '2', 'db_index': 'True'}),
            'text_body': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'to': ('django.db.models.fields.IntegerField', [], {'default': '497734'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': u"orm['contenttypes.ContentType']", 'null': 'True', 'blank': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['hipchat']
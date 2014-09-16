from __future__ import unicode_literals

# Django
from django.contrib import admin

# Local Apps
from .admin_base import BaseModelAdmin
from emails.admin import *
from grapevine.models import QueuedMessage


class QueuedMessageAdmin(BaseModelAdmin):
    list_display = ['id', 'message_type', 'message_id']


admin.site.register(QueuedMessage, QueuedMessageAdmin)

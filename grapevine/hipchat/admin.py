from __future__ import unicode_literals

# Django
from django.contrib import admin
from django.conf.urls import patterns, url
from django.core.urlresolvers import reverse

# Local Apps
from grapevine.admin import BaseModelAdmin
from .models import HipChat


class HipChatAdmin(BaseModelAdmin):
    pass

admin.site.register(HipChat, HipChatAdmin)

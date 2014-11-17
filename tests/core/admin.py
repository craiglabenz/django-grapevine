from __future__ import unicode_literals

# Django
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

# 3rd Party
from grapevine.admin_base import BaseModelAdmin, SendableInline
from grapevine.emails.admin import EmailableAdminMixin

# Local Apps
from .models import WelcomeEmail


class WelcomeEmailInline(SendableInline):
    model = WelcomeEmail


class UserAdmin(DjangoUserAdmin):
    inlines = [WelcomeEmailInline]


class WelcomeEmailAdmin(EmailableAdminMixin, BaseModelAdmin):
    raw_id_fields = ["user"]
    list_display = ["id", "user", "admin_message"]

    preview_height = 200

    fieldsets = (
        ('Main', {"fields": ("user",)},),
        ('Message', {"fields": ("admin_message", "scheduled_send_time",)},),
    )

admin.site.unregister(get_user_model())
admin.site.register(get_user_model(), UserAdmin)
admin.site.register(WelcomeEmail, WelcomeEmailAdmin)

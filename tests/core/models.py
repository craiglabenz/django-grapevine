from __future__ import unicode_literals

# Django
from django.conf import settings
from django.db import models

# 3rd Party
from grapevine import generics
from grapevine.models.base import GrapevineModel
from model_utils.managers import PassThroughManager

# Local Apps
from querysets import WelcomeEmailQuerySet


class WelcomeEmail(generics.EmailSendable, GrapevineModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="welcome_emails")

    try:
        # In Django 1.7, this is finally addressed!
        objects = WelcomeEmailQuerySet.as_manager()
    except AttributeError:
        # This handles Django <= 1.6
        objects = PassThroughManager.for_queryset_class(WelcomeEmailQuerySet)()

    class Meta:
        verbose_name = "Welcome Email"
        verbose_name_plural = "Welcome Emails"

    def __unicode__(self):
        return "Welcome Email to {0}".format(self.user.__unicode__())

    def get_template_name(self):
        return "Welcome Email"

    def get_raw_subject(self):
        return "Welcome to Acme Inc, {{ sendable.user }}!"

    def get_recipients(self):
        return {"to": [self.user.email], "bcc": ["top@secret.com"]}

    def confirm_individual_sendability(self):
        """Only send Welcome Emails to users with email addresses"""
        if not self.user.email:
            self.cancelled_at_send_time = True
            self.save()
        return bool(self.user.email)

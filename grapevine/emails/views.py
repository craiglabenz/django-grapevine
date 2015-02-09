from __future__ import unicode_literals

# Django
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.generic import View

# Local Apps
from grapevine.emails import models


class ViewEmailOnSite(View):

    def get(self, request, *args, **kwargs):
        email = get_object_or_404(models.Email, guid=kwargs.get("message_guid"))
        return HttpResponse(email.html_body)

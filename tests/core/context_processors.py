from __future__ import unicode_literals
import json

# Django
from django.conf import settings as _settings


def settings(request):
    return {
        'DEBUG': _settings.DEBUG,
    }

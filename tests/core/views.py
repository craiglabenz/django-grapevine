from __future__ import unicode_literals

# Django
from django.views.generic.base import TemplateView


class DummyView(TemplateView):
    template_name = "Landing Page"

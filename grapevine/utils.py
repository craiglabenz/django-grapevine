from __future__ import unicode_literals
import re

# Django
from django.shortcuts import render_to_response
from django.template import Template, Context, RequestContext


def render_view(request, template_name, context={}):
    return render_to_response(template_name, context, context_instance=RequestContext(request))


def simple_render(string, context, should_raise=True):
    """
    Renders a stringing against a context. For example, with the
    context: {"key", "value"}, the string "Hello, {{key}}!" would
    be converted to "Hello, value!"
    """
    return Template(string).render(Context(context))

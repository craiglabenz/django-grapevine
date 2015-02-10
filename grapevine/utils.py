from __future__ import unicode_literals
import re

# Django
from django.shortcuts import render_to_response
from django.template import Template, Context, RequestContext


def render_view(request, template_name, context={}):
    return render_to_response(template_name, context, context_instance=RequestContext(request))


def simple_render(string, context, should_raise=True, should_autoescape=True):
    """
    Renders a stringing against a context. For example, with the
    context: {"key", "value"}, the string "Hello, {{key}}!" would
    be converted to "Hello, value!"
    """
    string = Template(string).render(Context(context, autoescape=should_autoescape))

    if should_raise:
        # No-op if there are no placeholders
        regex = r'{{[^\s]*}}'  # standard {{token}} (no spaces)

        # Make sure we populated everything.
        matches = re.search(regex, string)
        if matches:
            raise ValueError("You failed to populate everything in `%s` !" % (string,))

    return string
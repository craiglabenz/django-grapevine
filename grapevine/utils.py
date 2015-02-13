from __future__ import unicode_literals
import re

# Django
from django.contrib.contenttypes.models import ContentType
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


class ContentTypeRepo(object):
    _instance = None
    ct_map = {}

    def __new__(cls, *args, **kwargs):
        """
        Singleton implementation
        """
        if not cls._instance:
            cls._instance = super(ContentTypeRepo, cls).__new__(cls, *args, **kwargs)
            cls._instance.seed_ct_map()
        return cls._instance

    def seed_ct_map(self):
        self.ct_map = {}
        for ct in ContentType.objects.all():
            self._instance.ct_map[ct.pk] = ct

    def get_content_type_by_id(self, id):
        return self.ct_map[id]

    def get_class_by_id(self, id):
        return self.get_content_type_by_id(id).model_class()


def valid_content_types():
    """
    Returns an iterator of only valid content types, using the ContentType
    lookup singleton above.
    """
    for pk, ct in ContentTypeRepo().ct_map.items():
        if bool(ct.model_class()):
            yield ct

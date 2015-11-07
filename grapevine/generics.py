from __future__ import unicode_literals

# Django
from django.conf import settings

# Local Apps
from grapevine import mixins


class EmailSendable(mixins.Emailable, mixins.SendableMixin):
    class Meta(mixins.SendableMixin.Meta):
        abstract = True


if 'tablets' in settings.INSTALLED_APPS:
    class EmailTemplateSendable(mixins.Emailable,
                                mixins.TemplateSendableMixin):
        class Meta(mixins.TemplateSendableMixin.Meta):
            abstract = True

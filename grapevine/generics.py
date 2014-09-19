from __future__ import unicode_literals

# Local Apps
from grapevine import mixins


class EmailSendable(mixins.Emailable, mixins.SendableMixin):
    class Meta(mixins.SendableMixin.Meta):
        abstract = True


class EmailTemplateSendable(mixins.Emailable,
                            mixins.TemplateSendableMixin):
    class Meta(mixins.TemplateSendableMixin.Meta):
        abstract = True

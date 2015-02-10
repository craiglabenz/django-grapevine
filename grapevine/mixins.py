from __future__ import unicode_literals

# Django
from django.db import models
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils import timezone
from django.template import Context
from django.template.loader import get_template
from django.utils import six
try:
    # This is the 1.7 import
    from django.contrib.contenttypes.fields import GenericRelation
except ImportError:
    # And this is the 1.6 import
    from django.contrib.contenttypes.generic import GenericRelation

# 3rd Party
import html2text
# from celery import shared_task

# Local Apps
from . import emails
from . import models as gv_models
from .managers import SendableManager
from .querysets import SendableQuerySet
from grapevine.decorators import memoize
from grapevine.utils import simple_render


class SendableMixin(models.Model):
    """
    Put this on models in other apps that are "sendable"

    Usage:
        # ``initial_data`` is whatever you need for your model
        sendable = SomeSendableClass.objects.create(**initial_data)
        sendable.send()
    """
    scheduled_send_time = models.DateTimeField(blank=True, default=None, null=True,
        db_index=True, verbose_name="Scheduled Send Time")
    cancelled_at_send_time = models.BooleanField(default=False, verbose_name="Cancelled at Send Time")
    message_id = models.PositiveIntegerField(db_index=True, blank=True, null=True,
        default=None, verbose_name="Message Id")

    objects = SendableManager.for_queryset_class(SendableQuerySet)()

    class Meta:
        abstract = True
        index_together = (
            ('scheduled_send_time', 'cancelled_at_send_time', 'message_id',),
        )

    def save(self, *args, **kwargs):
        # When creating, default ``scheduled_send_time`` to the callable
        if self.scheduled_send_time is None and not self.pk:
            self.scheduled_send_time = self.default_scheduled_send_time()
        return super(SendableMixin, self).save(*args, **kwargs)

    @property
    def is_sent(self):
        return bool(self.message_id)

    @property
    def is_spam(self):
        return self.is_sent and self.message.is_spam

    @property
    def is_opened(self):
        return self.is_sent and self.message.is_opened

    @property
    def is_clicked(self):
        return self.is_sent and self.message.is_clicked

    def get_absolute_url(self):
        if not self.message:
            # TODO: What to do here?
            return ""
        else:
            return reverse("grapevine:view-on-site", kwargs={"message_guid": self.message.guid})

    @property
    def message(self):
        """
        A helper property to ease getting of the associated message.
        """
        if hasattr(self, "_message"):
            return self._message

        if not self.is_sent:
            return None

        try:
            self._message = self.get_transport_class().objects.get(pk=self.message_id)
            return self._message
        except self.get_transport_class().DoesNotExist:
            # This should never happen!
            return None

    @message.setter
    def message(self, value):
        """
        A helper property to ease setting of the associated message.
        """
        self._message = value
        self.message_id = value.pk

    def denote_as_queued(self):
        """
        Once a message is in the queue, we store it in QueuedMessage to avoid
        the sender process continually re-queuing it until actual delivery.
        """
        queued_message, created = gv_models.QueuedMessage.objects.\
            get_or_create(message_type=self.get_content_type(), message_id=self.pk)
        return queued_message

    def delete_from_queue(self):
        """
        Once a message has passed through the queue and been delivered,
        we delete its QueuedMessage record. Note that this is *not* actually
        deleting the record from the real SQS queue.
        """
        gv_models.QueuedMessage.objects.\
            filter(message_type=self.get_content_type(), message_id=self.pk).delete()

    def default_scheduled_send_time(self):
        return timezone.now()

    def get_template(self, template_name=None):
        """
        Assumes a traditional Django, file system-based template loader
        """
        if template_name is None:
            template_name = self.get_template_name()
        return get_template(template_name)

    def get_template_name(self):
        raise NotImplementedError("%s failed to implemented `get_template_name`" % self.__class__.__name__)

    def compile_context(self):
        """
        This is the function classes using the SendableMixin should
        override to correctly populate their template.
        """
        return {
            'sendable': self,
            'view_on_site_uri': self.get_absolute_url(),
        }

    def get_context(self):
        """
        This function is used by Transport classes to render a template.
        As such, it should not need to be modified in any way by child classes.
        """
        if not hasattr(self, '_context'):
            self._context = self.compile_context()
        return self._context

    def _get_recipients(self, recipient_address=None):
        # Pass this in when sending test emails to override who
        # would normally receive this sendable.
        if recipient_address is not None:
            return recipient_address

        # If this is a real email and no explicit recipients have
        # been defined, fall back to what this Sendable defines.
        return self.get_recipients()

    def get_normalized_recipients(self):
        recipients = self.get_recipients()

        # Coerce them into a standard structure
        if isinstance(recipients, six.string_types):
            recipients = {"to": [recipients]}
        elif isinstance(recipients, list):
            recipients = {"to": recipients}
        elif isinstance(recipients, dict):
            for key, value in recipients.items():
                if isinstance(value, six.string_types):
                    recipients[key] = [value]

        return recipients

    def get_recipients(self):
        raise NotImplementedError("%s failed to implement `get_recipients`" % self.__class__.__name__)

    def get_raw_subject(self):
        """
        This function should return the raw subject with possible {{placeholder}}
        values still intact. They will be populated during `get_subject()` against
        self.context()
        """
        raise NotImplementedError("%s failed to implement `get_raw_subject`" % self.__class__.__name__)

    def get_subject(self):
        """
        Accepts the raw subject with possible placeholders and populates them
        against ``self.get_context()``.
        """
        # Get the raw subject
        subject = self.get_raw_subject()

        # Render and return
        return simple_render(subject, self.get_context())

    def get_raw_from_email(self):
        return settings.DEFAULT_FROM_EMAIL

    def get_from_email(self):
        from_email = self.get_raw_from_email()
        return simple_render(from_email, self.get_context())

    def get_raw_reply_to(self):
        return settings.DEFAULT_REPLY_TO

    def get_reply_to(self):
        reply_to = self.get_raw_reply_to()
        return simple_render(reply_to, self.get_context())

    @property
    def text_body(self):
        if not hasattr(self, '_text_body'):
            self._text_body = html2text.HTML2Text().handle(self.html_body)
        return self._text_body

    @property
    def html_body(self):
        """
        To avoid repeated rendering work, we cache the finalized value and
        access the html body through said cache whenever possible. Calling
        `render` outside of here should be a rare occurance.
        """
        if not hasattr(self, '_html_body'):
            self._html_body = self.render()
        return self._html_body

    @html_body.setter
    def html_body(self, value):
        self._html_body = value

    def render(self, template_name=None, context=None):
        """
        Gets ye some HTML
        """
        if context is None:
            context = self.get_context()

        template = self.get_template(template_name)
        return self._render(template, context)

    def _render(self, template, context):
        """
        Override hook for child classes.
        """
        return template.render(Context(context))

    def alter_transport(self, transport, **kwargs):
        """
        Hook for child classes to execute last-second operations on
        the Transport object.
        """
        return transport

    def get_transport_class(self):
        """
        Combine with transport-specific mixins to get this functionality.
        """
        raise NotImplementedError("%s class failed to implement ``get_transport_class``" % (self.__name__.__class__,))

    def as_transport(self, recipient_address=None, is_test=False, **kwargs):
        return self.get_transport_class().from_sendable(self, recipient_address=recipient_address,
            is_test=is_test, **kwargs)

    @staticmethod
    # @shared_task(queue="sendables")
    def async_send(cls, sendable_id, *args, **kwargs):
        sendable = cls.objects.get(id=sendable_id)
        return sendable.send(*args, **kwargs)

    def send(self, recipient_address=None, is_test=False, **kwargs):
        """
        Gets bits on the wire.

        Arguments
        @recipient_address  {str}   Override the recipient by supplying this value. Good for sending test emails.
        @is_test            {bool}  Set to True when overriding the recipient. A bookkeeping variable.
        """
        # Already sent messages shouldn't be resent.
        if not is_test and self.is_sent and not kwargs.pop('force_resend', False):
            # self.get_logger(decorated_class=SendableMixin).warning("Attempted to resend %s with Id %s", self.__class__.__name__, self.pk,)
            return False

        self.transport = self.as_transport(recipient_address=recipient_address,
            is_test=is_test, **kwargs)
        return self.transport.send()

    def send_test(self, recipient_address, **kwargs):
        kwargs['is_test'] = True
        return self.send(recipient_address=recipient_address, **kwargs)

    def confirm_individual_sendability(self):
        """
        Invoked by the actual sender job at the moment of sending.
        Extending classes can override this function and are encouraged,
        if they return False, to also push back ``self.scheduled_send_time``.

        Returns True to send, False to delay
        """
        return True


class TemplateSendableMixin(SendableMixin):
    """
    Exactly the same as the SendableMixin, except for how the message's
    actual content is determined.
    """
    template = models.ForeignKey('tablets.Template', blank=True, default=None, null=True)

    class Meta(SendableMixin.Meta):
        abstract = True

    def get_template_name(self):
        return self.template.name

    def get_raw_subject(self):
        if self.template.subject:
            return self.template.subject
        else:
            return super(TemplateSendableMixin, self).get_raw_subject()

    def get_raw_reply_to(self):
        reply_to = None

        # First ask the template for ``reply_to``
        if self.template:
            reply_to = self.template.reply_to

        # If the Template opted out, ask the model instance
        if not reply_to:
            reply_to = super(TemplateSendableMixin, self).get_raw_reply_to()

        # Lastly, fall back to the settings
        if not reply_to:
            reply_to = settings.DEFAULT_REPLY_TO

        return reply_to

    def get_raw_from_email(self):
        from_email = None

        # First ask the template for ``from_email``
        if self.template:
            from_email = self.template.from_email

        # If the Template opted out, ask the model instance
        if not from_email:
            from_email = super(TemplateSendableMixin, self).get_raw_from_email()

        # Lastly, fall back to the settings
        if not from_email:
            from_email = settings.DEFAULT_FROM_EMAIL

        return from_email

    def get_template(self, template_name=None):
        """
        For duck-typing purposes, this function must accept the ``template_name``
        param, though it makes no sense to do anything with it. We have a hard
        foreign key reference to a template record, and we will use that.
        """
        return self.template.as_template()


class Emailable(object):
    """
    Combine with any of the Sendable mixins to explicitly define which
    Transport class should be used.
    """

    @staticmethod
    def get_transport_class():
        return emails.models.Email

    def remove_unsubscribe_link(self, transport):
        transport.add_variable('should_show_unsubscribe_link', 0)
        return transport

    def track_clicks(self, transport):
        """
        Clicks appear to be tracked automatically.
        """
        transport.add_variable('should_track_clicks', 1)
        return transport

    def track_opens(self, transport):
        """
        Opens appear to be tracked automatically.
        """
        transport.add_variable('should_track_opens', 1)

    def add_ganalytic(self, transport, key, value):
        transport.add_variable('utm_%s' % (key,), value)
        return transport

from __future__ import unicode_literals
import uuid
import time
import traceback

# Django
from django.db import models
from django.conf import settings
from django.utils import timezone
# from django.contrib.contenttypes.models import ContentType
try:
    # This is 1.7
    from django.contrib.contenttypes.generic import GenericForeignKey
except ImportError:
    # This is the 1.6 import
    from django.contrib.contenttypes.fields import GenericForeignKey

# 3rd Party
import html2text

# Local Apps
from .models_base import GrapevineModel


class Transport(GrapevineModel):
    """
    The abstract parent class for all various modes of Sendable transportation.
    """
    SENT = 1
    UNSENT = 2
    FAILED = 3
    SEND_TIME_ERROR = 4
    NEWSLETTER = 5
    DUPLICATE = 6
    UNSUBSCRIBED = 7
    STATUS_CHOICES = (
        (SENT, 'Sent',),
        (FAILED, 'Failed',),
        (UNSENT, 'Unsent',),
        (SEND_TIME_ERROR, 'Send-time Error',),
        (NEWSLETTER, 'Newsletter',),
        (DUPLICATE, 'Duplicate',),
        (UNSUBSCRIBED, 'Unsubscribed',),
    )

    type = models.ForeignKey('contenttypes.ContentType', blank=True, null=True, default=None)
    html_body = models.TextField(blank=True)
    text_body = models.TextField(blank=True)
    status = models.IntegerField(choices=STATUS_CHOICES, default=UNSENT, db_index=True)
    sent_at = models.DateTimeField(db_index=True, verbose_name='Sent At', null=True, default=None, blank=True)
    communication_time = models.DecimalField(max_digits=8, decimal_places=5, null=True, blank=True, default=None,
        verbose_name="Communication Time", help_text="In seconds")
    is_test = models.BooleanField(default=False, verbose_name='Is Test', db_index=True)
    guid = models.CharField(max_length=36, null=True, blank=True, db_index=True)
    log = models.TextField(blank=True, null=True, default=None)

    class Meta(GrapevineModel.Meta):
        abstract = True

    def ensure_guid(self):
        if not (self.guid):
            self.guid = str(uuid.uuid4())
        return self

    @property
    def sendable_class(self):
        return self.type.model_class()

    @property
    def sendable(self):
        if not hasattr(self, '_sendable'):
            try:
                self._sendable = self.sendable_class.objects.get(message_id=self.pk)
            except:
                # Purposefully don't cache self._sendable here to allow
                # future code (after this message is sent) to accurately
                # return the ``sendable`` obj
                return None
        return self._sendable

    def determine_text_body(self):
        if not bool(self.text_body):
            self.text_body = html2text.html2text(self.html_body)

    def save(self, *args, **kwargs):
        """
        Enforces some code-heavy (not so much DB-heavy) defaults, then saves.
        """
        # New message records get GUIDs
        self.ensure_guid()

        # Didn't supply a plain text value? You get a converted version
        # from your HTML value for free.
        self.determine_text_body()

        self.pre_save(*args, **kwargs)
        super(Transport, self).save(*args, **kwargs)
        self.post_save(*args, **kwargs)

    def pre_save(self, *args, **kwargs):
        pass

    def post_save(self, *args, **kwargs):
        pass

    def send(self, *args, **kwargs):
        try:
            # Put a stopwatch on the actual communication
            start = time.time()

            is_sent = self._send(*args, **kwargs)

            end = time.time()
            self.communication_time = (end - start)

            # Now that the message has been sent, delete it from
            # the queue to keep lookups to that table nice and fast
            if self.sendable:
                self.sendable.delete_from_queue()

            if is_sent:
                self.status = self.SENT
                self.sent_at = timezone.now()
            else:
                # Honor any status setting that may have happened
                # during ``_send()``
                if self.status == self.UNSENT:
                    self.status = self.FAILED

            self.save()
            return is_sent
        except Exception as e:
            stack = traceback.extract_stack()
            formatted_stack = '\n'.join(traceback.format_list(stack))

            self.status = self.SEND_TIME_ERROR
            self.append_to_log(formatted_stack, should_save=False, desc=e.args[0])
            self.save()
            return False

    def _send(self, *args, **kwargs):
        """
        Actual bits onto the wire fun. Must be implemented by non-abstract
        Transport subclasses.
        """
        raise NotImplementedError("%s class has not implemented ``_send``" % (self.__class__.__name__,))

    @classmethod
    def from_sendable(cls, sendable, recipient_address=None, is_test=False, **kwargs):
        """
        Given an instance of a Sendable, this builds a corresponding instance of
        whichever child ``transport`` class this ultimately is.

        Arguments:
        @sendable           {mixed} An instance of a class using the SendableMixin
        @recipient_address  {str}   A recipient-override option. Useful in conjunction
                                    with `is_test`.
        @is_test            {bool}  A bookkeeping variable to quickly see if this message
                                    was a test.
        """
        initial_data = {
            'type': sendable.content_type(),
            'to': sendable._get_recipients(recipient_address),
            'html_body': sendable.html_body,
            'text_body': sendable.text_body,
            'status': cls.UNSENT,
            'is_test': is_test,
        }
        initial_data = cls.finish_initial_data(sendable, initial_data, **kwargs)
        transport = cls.objects.create(**initial_data)

        # Save the link between sendable and message
        if not is_test:
            sendable.message_id = transport.pk
            sendable.save()

        # Allow the Sendable object to make last second
        # modifications to the Transport. This may include
        # adding tags, altering attributes, etc.
        transport = sendable.alter_transport(transport, **kwargs)

        return transport

    @staticmethod
    def finish_initial_data(sendable, data, **kwargs):
        """
        Hook for using classes to optionally augment the initial data given
        to their Transport object.
        """
        return data


class QueuedMessage(GrapevineModel):
    """
    Records are written to this table when a message is queued, and
    subsequently deleted when the message is ultimately sent.
    """

    message_type = models.ForeignKey('contenttypes.ContentType', verbose_name="Message Type")
    message_id = models.PositiveIntegerField(verbose_name="Message Id")

    message = GenericForeignKey('message_type', 'message_id')

    class Meta:
        verbose_name = "Queued Message"
        verbose_name_plural = "Queued Messages"

    def unicode(self):
        return 'Queued Message %s:%s' % (self.message_type_id, self.message_id,)

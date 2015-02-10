from __future__ import unicode_literals

# Django
from django.db import models
from django.conf import settings
from django.utils import timezone, six, module_loading
from django.core.mail import get_connection, EmailMultiAlternatives

# 3rd Party
# from celery import shared_task

# Local Apps
from utils import parse_email, EventRepo
from managers import EmailManager, EmailRecipientManager
from grapevine.decorators import memoize
from grapevine.models.base import GrapevineModel
from grapevine.models import Transport
from grapevine.settings import grapevine_settings


class Email(Transport):
    """
    The grand central email table.

    Direct Usage:
            # FIRST
        email = Email.objects.create(
                    html_body="<p>Hello, world.</p>",
                    from_email="Support Team <support@acmetech.com>",  * Optional, defaults to settings
                    reply_to="specific-reply-address@acmetech.com",
                    subject="Welcome to Acme Tech!",
                    backend="path.to.backend.EmailBackend", # OPTIONAL.
                    to=[
                        'tos': ["some@email.com", "Frank the Tank <frank@thetank.com", ...],
                        'ccs': ["account-admin1@domain.com", "account-admin2@domain.com", ...]
                        'bccs': "alerts@acmetech.com"  * Could also be a list like above
                    ]
                )

            # THEN....
        email.send()

    """
    backend = models.ForeignKey('EmailBackend', blank=True)
    from_email = models.CharField(max_length=255, db_index=True, default=settings.DEFAULT_FROM_EMAIL)
    reply_to = models.EmailField(max_length=255, blank=True, default=settings.DEFAULT_REPLY_TO)
    subject = models.CharField(max_length=255, default=settings.DEFAULT_SUBJECT)

    objects = EmailManager()

    class Meta:
        app_label = "emails"
        verbose_name = 'Email'
        verbose_name_plural = 'Emails'

    def __unicode__(self):
        recipient = ''

        main_recipient = self.get_main_recipient()
        if main_recipient:
            recipient = ' %s: ' % (main_recipient.__unicode__(),)
        if self.pk:
            return '%s (%s)' % (recipient, self.subject[:50],)
        else:
            return 'Unsaved Email:%s (%s)' % (recipient, self.subject[:50],)

    def get_main_recipient(self):
        if hasattr(self, "main_recipient"):
            return self.main_recipient

        try:
            self.main_recipient = self.recipients.all()[0]
        except IndexError:
            self.main_recipient = None

        return self.main_recipient

    def save(self, *args, **kwargs):
        if not self.backend_id:
            self.backend, created = EmailBackend.objects.get_or_create(path=grapevine_settings.EMAIL_BACKEND)

        super(Email, self).save(*args, **kwargs)

    @staticmethod
    def determine_backend(**kwargs):
        if 'backend_id' in kwargs.keys():
            key = 'backend_id'
            backend = kwargs['backend_id']
        elif 'backend' in kwargs.keys():
            key = 'backend'
            if isinstance(kwargs['backend'], six.string_types):
                backend, created = EmailBackend.objects.get_or_create(path=kwargs['backend'])
            else:
                backend = kwargs['backend']
        else:
            key = backend = None
        return key, backend

    @staticmethod
    def extra_transport_data(sendable, **kwargs):
        extra_data = {
            'from_email': sendable.get_from_email(),
            'reply_to': sendable.get_reply_to(),
            'subject': sendable.get_subject(),
        }

        # Honor a custom EmailBackend request
        key, backend = Email.determine_backend(**kwargs)
        if backend is not None:
            extra_data[key] = backend

        return extra_data

    def add_tos(self, recipients):
        """
        Args:
        @recipients  {list}   A list of email addresses (strings) that should receive ziss email
        """
        # Cast to a list
        if not isinstance(recipients, list):
            recipients = [recipients]

        for recipient in recipients:
            self.add_recipient(recipient, EmailRecipient.TO)

    def add_ccs(self, recipients):
        """
        Args:
        @recipients  {list}   A list of email addresses (strings) that should receive ziss email
        """
        # Cast to a list
        if not isinstance(recipients, list):
            recipients = [recipients]

        for recipient in recipients:
            self.add_recipient(recipient, EmailRecipient.CC)

    def add_bccs(self, recipients):
        """
        Args:
        @recipients  {list}   A list of email addresses (strings) that should receive ziss email
        """
        # Cast to a list
        if not isinstance(recipients, list):
            recipients = [recipients]

        for recipient in recipients:
            self.add_recipient(recipient, EmailRecipient.BCC)

    def add_recipient(self, recipient, recipient_type):
        """
        Args:
        @recipient      {str}   The email to receive this msg
        @recipient_type {int}   Maps to EmailRecipient.TYPES
        """
        return EmailRecipient.objects.create(email=self, address=recipient, type=recipient_type)

    def add_recipients(self, recipients):
        """
        Accepts and saves recipients in a smorgasboard of formats
        """
        if isinstance(recipients, six.string_types):
            return self.add_tos([recipients])
        elif isinstance(recipients, list):
            return self.add_tos(recipients)
        elif isinstance(recipients, dict):
            # Dicts should have keys "to", "cc", and "bcc"
            self.add_tos(recipients.get('to', []))
            self.add_ccs(recipients.get('cc', []))
            self.add_bccs(recipients.get('bcc', []))
        else:
            raise ValueError("`recipients` must be a str, list, or dict")

    def add_variable(self, key, value):
        return EmailVariable.objects.create(email=self, key=key, value=value)

    @property
    def to(self):
        return [er.prepare_for_email() for er in EmailRecipient.objects.filter(email=self, type=EmailRecipient.TO)]

    @property
    def cc(self):
        return [er.prepare_for_email() for er in EmailRecipient.objects.filter(email=self, type=EmailRecipient.CC)]

    @property
    def bcc(self):
        return [er.prepare_for_email() for er in EmailRecipient.objects.filter(email=self, type=EmailRecipient.BCC)]

    def _send(self, backend=None, fail_silently=False, **kwargs):
        """
        Loads up the EmailBackend class to finally talk to an EMAIL_BACKEND
        """
        return self.backend.send(self, fail_silently, **kwargs)

    @property
    @memoize
    def is_spam(self):
        return self.find_event_by_name('Spam Report')

    @property
    @memoize
    def is_opened(self):
        return self.find_event_by_name('Open')

    @property
    @memoize
    def is_clicked(self):
        return self.find_event_by_name('Click')

    @property
    @memoize
    def cached_events(self):
        return [event for event in self.events.all()]

    def find_event_by_name(self, name):
        event_type = EventRepo()[name]
        for email_event in self.cached_events:
            if email_event.event_id == event_type.pk:
                return True
        return False


class EmailRecipient(GrapevineModel):

    TO = 1
    CC = 2
    BCC = 3
    TYPES = (
        (TO, 'To',),
        (CC, 'CC',),
        (BCC, 'BCC',),
    )

    email = models.ForeignKey(Email, db_index=True, related_name='recipients')
    # https://docs.djangoproject.com/en/1.6/ref/models/fields/#emailfield
    address = models.EmailField(max_length=254, db_index=True, verbose_name='Recipient Address')
    domain = models.CharField(max_length=100, db_index=True)
    name = models.CharField(max_length=150, blank=True)
    type = models.IntegerField(choices=TYPES, default=TO)

    objects = EmailRecipientManager()

    class Meta:
        app_label = "emails"
        verbose_name = 'Email Recipient'
        verbose_name_plural = 'Email Recipients'

    def __unicode__(self):
        return '%s: %s' % (self.email.pk, self.prepare_for_email(),)

    def prepare_for_email(self):
        if self.name:
            return '%s <%s>' % (self.name, self.address,)
        else:
            return self.address

    def determine_domain(self):
        if not bool(self.domain):
            self.domain = self.address.split('@')[1].lower()

    def save(self, *args, **kwargs):
        self.determine_domain()
        super(EmailRecipient, self).save(*args, **kwargs)


class EmailBackend(GrapevineModel):
    name = models.CharField(max_length=255)
    path = models.CharField(max_length=255, help_text="The dotted import path to this backend, in "
                               "a structure that would satisfy settings.EMAIL_BACKEND.")
    username = models.CharField(max_length=255, blank=True, help_text="Depending on the provider, this "
                               "may actually be an API key.")
    password = models.CharField(max_length=255, blank=True, help_text="Depending on the provider, this "
                               "may actually be an API secret.")

    class Meta:
        app_label = "emails"
        verbose_name = "Email Backend"
        verbose_name_plural = "Email Backends"

    @property
    def kls(self):
        return module_loading.import_by_path(dotted_path=self.path)

    def __unicode__(self):
        if self.name:
            return self.name
        else:
            return self.path

    def get_connection(self, fail_silently=False, **kwargs):
        """
        Keyword Arguments:
        @backend        {str}   The dotted path to a fully functional Django emailer backend.
                                Defaults to ``settings.EMAIL_BACKEND`` if not passed.
        @fail_silently  {bool}  Whether or not to raise problems.
        """
        if self.username:
            kwargs.setdefault('username', self.username)
        if self.password:
            kwargs.setdefault('password', self.password)

        return get_connection(backend=self.path, fail_silently=fail_silently, **kwargs)

    def get_headers(self, email):
        return {
            'reply_to': email.reply_to,
        }

    def as_message(self, email):
        """
        Django email code relies on a combination of the EMAIL_BACKEND
        class itself and an instance of a message-style class that the
        backend uses to build the actual payload.

        This function is an opportunity for EMAIL_BACKENDs to hook in
        and create a Message object of its own designs.
        """
        import backends
        is_grapevine_backend = issubclass(self.kls, backends.base.GrapevineEmailBackend)
        implements_as_message = hasattr(self.kls, 'as_message')

        if is_grapevine_backend and implements_as_message:
            # Provider-specific EMAIL_BACKENDS will
            # likely implement this method and thus create their
            # own "message" obj
            msg = self.kls.as_message(email)
        else:
            # OTS Django or other SMTP-based EMAIL_BACKENDS will use
            # this standard functionality
            msg = EmailMultiAlternatives(
                subject=email.subject,
                body=email.text_body,
                from_email=email.from_email,
                to=email.to,
                cc=email.cc,
                bcc=email.bcc,
                headers=self.get_headers(email),
            )
            if email.html_body:
                msg.attach_alternative(email.html_body, "text/html")

        msg._email = email
        return msg

    def finalize_message(self, message):
        # Honor unsubscribes and DEV settings
        if hasattr(self.kls, 'finalize_message'):
            return self.kls.finalize_message(message)
        else:
            # The base implementation of this function works for Django's
            # ``EmailMessage`` class
            import backends
            return backends.base.GrapevineEmailBackend.finalize_message(message)

    def send(self, email, fail_silently=False, **kwargs):
        """
        Does a handful of things seen in Django's own wrapper around
        EMAIL_BACKENDS, found at ``django.core.mail.send_mail``.
        """
        kwargs.setdefault('fail_silently', fail_silently)

        # Convert our Grapevine ``Email`` obj into something this
        # specific backend can use
        msg = self.as_message(email)

        # Pass old school EmailMessage instances to
        # the Base finalizer to honor Unsubscribes and such
        msg = self.finalize_message(msg)

        if len(msg.to) == 0:
            self.get_logger().info("Not sending Email Id:%s due to all `TO` recipients having unsubscribed.", email.pk)
            email.status = email.UNSUBSCRIBED
            email.save()
            return False

        # Initialize an instance of the Backend class
        msg.connection = self.get_connection(**kwargs)

        # Fly birdies!
        # http://img3.wikia.nocookie.net/__cb20110615180140/gameofthrones/images/1/18/Bronn_defeats_Vardis.jpg
        is_sent = self._send(msg, **kwargs)

        msg.connection.close()

        if not is_sent:
            if getattr(msg, "failure_reason", False):
                print msg.failure_reason
                email.append_to_log(msg.failure_reason)
            else:
                print "no failure_reason"

        return is_sent

    def _send(self, msg, **kwargs):
        """
        Like ``as_message``, this is a hook for a specific driver to
        optionally take control of a piece of the fun.

        Finally gets bits onto the wire.
        """
        if hasattr(msg.connection, 'send'):
            return msg.connection.send(msg)
        else:
            return msg.send(**kwargs)


class EmailVariable(GrapevineModel):

    email = models.ForeignKey(Email, related_name="variables")
    key = models.CharField(max_length=100)
    value = models.CharField(max_length=5000, blank=True, help_text="1 represents True, and 0 represents False.")

    class Meta:
        app_label = "emails"
        verbose_name = "Email Variable"
        verbose_name_plural = "Email Variables"

        index_together = (
            ('key', 'value',),
        )

    def __unicode__(self):
        if self.value:
            return "%s: %s %s" % (self.email.__unicode__(), self.key, self.value,)
        else:
            return "%s: %s" % (self.email.__unicode__(), self.key,)


class RawEvent(GrapevineModel):

    backend = models.ForeignKey(EmailBackend)
    payload = models.TextField()
    processed_on = models.DateTimeField(null=True, default=None, blank=True,
        verbose_name="Processed On")
    processed_in = models.DecimalField(max_digits=5, decimal_places=4, blank=True,
        null=True, default=None, verbose_name="Processed In")
    is_queued = models.BooleanField(default=False, db_index=True, verbose_name="Is Queued")

    # Email providers do not often send payloads in formats that match
    # their documentation
    is_broken = models.NullBooleanField(default=None, db_index=True, verbose_name="Is Broken")

    # Bookkeeping
    remote_ip = models.GenericIPAddressField(db_index=True, verbose_name="Remote IP")

    class Meta:
        app_label = "emails"
        verbose_name = "Raw Event"
        verbose_name_plural = "Raw Events"

    @staticmethod
    # @shared_task
    def async_process(raw_event_id):
        raw_event = RawEvent.objects.get(pk=raw_event_id)
        raw_event.process()

    def process(self):
        is_processed, time_taken = self.backend.kls().process_event(self)
        # Not queued anymore, obviously
        self.is_queued = False

        if is_processed:
            self.processed_on = timezone.now()
            self.processed_in = time_taken
        else:
            self.is_broken = True
        self.save()


class Event(GrapevineModel):
    name = models.CharField(max_length=100)
    should_stop_sending = models.BooleanField(default=False,
        verbose_name="Should Stop Sending")

    class Meta:
        app_label = "emails"
        verbose_name = "Event"
        verbose_name_plural = "Events"

    def __unicode__(self):
        return self.name


class EmailEvent(GrapevineModel):

    email = models.ForeignKey(Email, related_name="events")
    event = models.ForeignKey(Event, related_name="email_events")
    raw_event = models.ForeignKey(RawEvent, verbose_name="Raw Event", related_name="email_events")
    happened_at = models.DateTimeField(db_index=True, verbose_name="Happened At")

    class Meta:
        app_label = "emails"
        verbose_name = "Email Event"
        verbose_name_plural = "Email Events"

    def __unicode__(self):
        return '%s Email Id: %s' % (self.event.__unicode__(), self.email_id,)


class UnsubscribedAddress(GrapevineModel):
    address = models.CharField(max_length=255, db_index=True)
    email = models.ForeignKey(Email, null=True, blank=True, default=None,
        help_text="Optional link back to the Email in which this recipient address \
        clicked Unsubscribe.", related_name="unsubscribed_addresses")

    class Meta:
        app_label = "emails"
        verbose_name = "Unsubscribed Address"
        verbose_name_plural = "Unsubscribed Addresses"

    def __unicode__(self):
        return self.address

    def save(self, *args, **kwargs):
        """
        Parses out formatted email addresses into raw thangs
        """
        name, self.address = parse_email(self.address)
        return super(UnsubscribedAddress, self).save(*args, **kwargs)

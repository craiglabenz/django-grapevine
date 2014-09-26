from __future__ import unicode_literals
import time
import json

# Django
from django.conf import settings
from django.core.mail.message import EmailMessage
from django.db import transaction

# 3rd Party
# from celery import shared_task
try:
    # This library isn't absolutely required until you
    # want to use the SendGrid backend
    import sendgrid
except ImportError:
    pass


# Local Apps
from .base import GrapevineEmailBackend
from grapevine.settings import grapevine_settings
from grapevine.emails import models as email_models


class EmailBackend(GrapevineEmailBackend):

    DISPLAY_NAME = "sendgrid"
    IMPORT_PATH = "grapevine.emails.backends.SendGridEmailBackend"

    # These are SendGrid variables that have a simple format of
    # `name` - enabled - {0|1}
    SIMPLE_VARIABLE_MAP = {
        "should_show_unsubscribe_link": "subscriptiontrack",
        "should_track_clicks": "clicktrack",
        "should_track_opens": "opentrack"
    }

    # Keys here are SendGrid event names, values are
    # Grapevine event names
    EVENTS_MAP = {
        # Only need to list values here that do not map
        # exactly (after first letter capitalization)
        "spamreport": "Spam Report"
    }

    UNIQUE_ARG_NAME = 'grapevine-guid'

    def __init__(self, fail_silently=False, username=None, password=None, **kwargs):
        # Sets ``self.fail_silently``
        super(EmailBackend, self).__init__(fail_silently=fail_silently)

        try:
            self.username = username or getattr(settings, 'SENDGRID_USERNAME')
            self.password = password or getattr(settings, 'SENDGRID_PASSWORD')
        except AttributeError:
            if fail_silently:
                self.username, self.password = None
            else:
                raise

        self.driver = sendgrid.SendGridClient(self.username, self.password,
            # Don't pass ``not self.fail_silently`` here, as that triggers
            # Exceptions to be raised in the SendGrid code instead of just
            # returning the response, which we would strongly prefer.
            raise_errors=False)

    @classmethod
    def debugify_message(cls, message):
        message.set_tos([grapevine_settings.DEBUG_EMAIL_ADDRESS])
        message.to = [grapevine_settings.DEBUG_EMAIL_ADDRESS]
        message.bcc = []
        return message

    @staticmethod
    def as_message(email):
        """
        Takes a ``grapevine.emails.Email`` model and converts it
        into a ``sendgrid.Mail`` object.
        """
        message = sendgrid.Mail()
        message.add_to(email.to)
        message.add_to(email.cc)
        message.add_bcc(email.bcc)
        message.set_text(email.text_body)
        message.set_html(email.html_body)
        message.set_subject(email.subject)
        message.set_from(email.from_email)
        message.set_replyto(email.reply_to)

        # Grapevine GUID
        message.add_unique_arg(EmailBackend.UNIQUE_ARG_NAME, email.guid)

        for variable in email.variables.all():
            if not bool(variable.value):
                message.add_category(variable.key)
            else:
                if variable.key in EmailBackend.SIMPLE_VARIABLE_MAP.keys():
                    sendgrid_key = EmailBackend.SIMPLE_VARIABLE_MAP[variable.key]
                    message.add_filter(sendgrid_key, 'enabled',
                        int(variable.value))
                elif variable.key[:4] == 'utm_':
                    message.add_filter('ganalytics', 'enabled', 1)
                    message.add_filter('ganalytics', variable.key, variable.value)

        return message

    def from_django_message(self, django_message):
        """
        Converts a ``django.core.mail.messages.EmailMessage`` into a
        ``grapevine.emails.Email`` object, then in turn into a
        ``sendgrid.Mail`` object.
        """
        initial_data = {
            'backend': 'grapevine.emails.backends.SendGridEmailBackend',
            'from_email': django_message.from_email,
            'subject': django_message.subject,
            'text_body': django_message.body,
        }
        if 'reply-to' in django_message.extra_headers:
            initial_data['reply_to'] = django_message.extra_headers.pop('reply-to')

        email = email_models.Email.objects.create(**initial_data)

        email.add_tos(django_message.to)
        email.add_ccs(django_message.cc)
        email.add_bccs(django_message.bcc)

        return self.as_message(email)

    def send_messages(self, email_messages):
        """
        Loops over a list (or single instance) of a Message object
        and sends said message using SendGrid's officially provided
        Python library.
        """
        if not isinstance(email_messages, list):
            email_messages = [email_messages]

        num_sent = 0
        for email_message in email_messages:
            if self.send(email_message):
                num_sent += 1

        return num_sent

    def send(self, email_message):
        """
        Sends a payload to SendGrid. Note that if ``self.fail_silently`` is False
        then the SendGrid library does not bother to return True on a successful
        send, as the lack of a raised Exception signifies a successful send.
        """
        # Cast a raw Django message obj as a Grapevine email. Note that this
        # is only possible if someone uses's Django's off-the-shelf ``send_mail``
        # function with this backend. In that case, the developer sacrifices
        # honoring of their ``UnsubscribedAddress`` list and DEBUG mode logic.
        if isinstance(email_message, EmailMessage):
            email_message = self.from_django_message(email_message)

        # Finally... we pass the email_message object to SendGrid's library
        self.send_response_code, self.send_response_body = self.driver.send(email_message)

        # Arbitrarily return True if ``self.fail_silently``, otherwise
        # only return True if SendGrid agrees that it worked
        return self.fail_silently or self.send_response_code == 200

    def get_event(self, sendgrid_event_name):
        if sendgrid_event_name in self.EVENTS_MAP.keys():
            return self.EVENTS_MAP[sendgrid_event_name]
        else:
            return sendgrid_event_name.capitalize()

    def process_events(self, limit=300):
        self.get_logger().debug("Beginning async_process_events with limit=%s" % limit)
        try:
            # Get the backend obj
            sendgrid_backend = email_models.EmailBackend.objects.filter(path="grapevine.emails.backends.SendGridEmailBackend")[0]
        except IndexError:
            # If there's not even a SendGrid record in the DB then we haven't sent any emails
            # through it and we don't have to worry about processing events
            return None

        with transaction.atomic():
            event_pks = email_models.RawEvent.objects.filter(
                backend=sendgrid_backend,
                processed_on=None,
                is_queued=False).exclude(is_broken=True).values_list('pk', flat=True)[:limit]

            # We must turn this queryset into a raw list of IDs, lest our
            # update to queue the events means eventual outright evaluation
            # of the queryset will re-run the query and return incorrect  records
            event_pks = [event_pk for event_pk in event_pks]

            email_models.RawEvent.objects.filter(pk__in=event_pks).update(is_queued=True)

        for event_pk in event_pks:
            email_models.RawEvent.async_process.delay(event_pk)

    def process_event(self, raw_event):
        """
        Arguments:
        @raw_event  {email_models.RawEvent}  That which we shall process.

        Returns  (bool, float,)   Success flag, time_taken
        """
        start = time.time()

        try:
            # Load the JSON into a dict, return False
            # if we have any problems
            payload = json.loads(raw_event.payload)
        except:
            return False, None

        for raw_event_dict in payload:

            try:
                # We can only process an event containing a
                # known Grapevine guid
                guid = raw_event_dict[self.UNIQUE_ARG_NAME]
            except KeyError:
                continue

            # Figure out which event it is that happened
            event_name = self.get_event(raw_event_dict['event'])
            try:
                event_type = email_models.Event.objects.get(name=event_name)
            except email_models.Event.DoesNotExist:
                continue

            # To which email in our system does this correspond?
            try:
                email = email_models.Email.objects.get(guid=guid)
            except email_models.Email.DoesNotExist:
                # Alarming, but not really anything to do.
                # STOP DELETING RECORDS!
                continue

            # Mint the event record
            email_event, created = email_models.EmailEvent.objects.get_or_create(email=email,
                event=event_type, raw_event=raw_event, happened_at=self.datetime_from_seconds(raw_event_dict['timestamp']))

            # Mark the email address as "Unsubscribed" if it's that kind of Event
            if event_type.should_stop_sending and raw_event_dict.get('email', None):
                email_models.UnsubscribedAddress.objects.create(address=raw_event_dict['email'],
                    email=email)

            # Note the event in the Email's direct log
            email.append_to_log(json.dumps(raw_event_dict))

        return True, (time.time() - start)

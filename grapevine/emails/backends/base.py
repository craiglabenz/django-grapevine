from __future__ import unicode_literals
import datetime

# Django
from django.conf.urls import url
from django.core.mail.backends.base import BaseEmailBackend
from django.http import HttpResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

# Local Apps
from grapevine.settings import grapevine_settings
from grapevine.emails import models as email_models
from grapevine.emails.utils import parse_email


class GrapevineEmailBackend(BaseEmailBackend):
    # Used to register a callback url for the 3rd party
    DISPLAY_NAME = None

    # Used to process catalog events
    IMPORT_PATH = None

    LISTENS_FOR_EVENTS = True

    def get_urls(self):
        urls = []
        if self.LISTENS_FOR_EVENTS:
            urls.append(
                url(r'^backends/{0}/events/$'.format(self.DISPLAY_NAME), self.events_webhook, name="{0}-events-webhook".format(self.DISPLAY_NAME)),
            )
        return urls

    def process_event(self, event):
        """
        This method must only be implemented if this backend
        communicates with a specific email sending provider that
        offers webhooks for email events.
        """
        raise NotImplementedError()

    def datetime_from_seconds(self, timestamp):
        """
        Takes a timestamp (like 1337966815) and turns it into
        something like this: datetime.datetime(2012, 5, 16, 15, 46, 40, tzinfo=<UTC>)
        """
        datetime_obj = datetime.datetime.utcfromtimestamp(timestamp)
        return timezone.make_aware(datetime_obj, timezone.get_default_timezone())

    @classmethod
    def debugify_message(cls, message):
        message.to = [grapevine_settings.DEBUG_EMAIL_ADDRESS]
        message.cc = []
        message.bcc = []

        return message

    @classmethod
    def finalize_message(cls, message):
        """
        Where the ``DEBUG`` setting and unsubscribe list are honored.

        Note that this works for the Django ``EmailMessage`` class as well
        as the SendGrid ``mail.Mail()`` class, as the two store recipients
        internally the same way.
        """
        # Strip out all recipients if this is a (localhost-style)
        # TEST_EMAIL.
        if grapevine_settings.DEBUG:
            message = cls.debugify_message(message)

        # Compile a grand list of all recipient lists
        recipient_lists = [getattr(message, 'to', []), getattr(message, 'cc', []), getattr(message, 'bcc', [])]
        for recipient_list in recipient_lists:
            indicies_to_pop = []
            for index, recipient in enumerate(recipient_list):
                try:
                    # Remove any remaining unsubscribed emails
                    name, address = parse_email(recipient)
                    unsubscribed = email_models.UnsubscribedAddress.objects.get(
                        address=address
                    )
                    indicies_to_pop.append(index)
                except email_models.UnsubscribedAddress.DoesNotExist:
                    pass

            # Must loop over this list in reverse to not change
            # the indicies of elements after the one's we remove
            indicies_to_pop.reverse()
            for index in indicies_to_pop:
                recipient_list.pop(index)

        return message

    @csrf_exempt
    def events_webhook(self, request):
        """
        Responds to {POST /grapevine/backends/:DISPLAY_NAME/events/}
        """
        # Using the ``require_POST`` decorator causes problems
        if request.method != 'POST':
            return HttpResponse(status=405)

        try:
            backend = email_models.EmailBackend.objects.filter(path=self.IMPORT_PATH)[0]
        except IndexError:
            backend = email_models.EmailBackend.objects.create(path=self.IMPORT_PATH)

        # Pull out the payload from request.POST as per
        # https://docs.djangoproject.com/en/1.6/ref/request-response/#django.http.HttpRequest.POST
        email_models.RawEvent.objects.create(backend=backend, payload=request.body,
                                             remote_ip=request.META['REMOTE_ADDR'])

        # A 200 tells SendGrid we successfully accepted this event payload
        return HttpResponse(status=200)

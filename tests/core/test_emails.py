# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import datetime
import mock
import requests

# Django
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import EmailMultiAlternatives
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.utils import override_settings
from django.utils import timezone

# 3rd Party
from grapevine.generics import EmailSendable
from grapevine.settings import grapevine_settings
from grapevine.emails.backends import MailGunEmailBackend
from grapevine.emails.models import Email, EmailRecipient, \
    EmailBackend, EmailVariable, UnsubscribedAddress, RawEvent

# Local Apps
from .factories import UserFactory, EmailFactory, SendGridEmailFactory
from core import models

try:
    import sendgrid
except ImportError:
    sendgrid = None


class RecipientsTester(TestCase):
    """
    Tests all things Recipient-setting related.
    """

    def setUp(self):
        self.em = Email.objects.create(type=models.WelcomeEmail.get_content_type())

    def test_add_to(self):
        """
        Though `add_tos` mostly deals in lists, it should also accept a
        single email address.
        """
        self.em.add_tos('marco@polo.com')

        self.assertEquals(len(self.em.to), 1)
        self.assertEquals(EmailRecipient.objects.filter(email=self.em, type=EmailRecipient.TO).count(), 1)

    def test_add_formatted_name(self):
        """
        Adds a single formatted email address.
        """
        self.em.add_tos('Marco Polo <marco@polo.com>')
        self.assertEquals(len(self.em.to), 1)

        rec = EmailRecipient.objects.filter(email=self.em)[0]
        self.assertEquals(rec.address, 'marco@polo.com')
        self.assertEquals(rec.name, 'Marco Polo')
        self.assertEquals(rec.domain, 'polo.com')

    def test_add_non_ascii_formatted_name(self):
        """
        Non-ASCII characters shouldn't cause a conniption.
        CUZ THAT'S NOT COOL OKAY GAWSH.
        """
        self.em.add_tos('Grisel Peña <grisel@peña.com>')
        self.assertEquals(len(self.em.to), 1)

        rec = EmailRecipient.objects.filter(email=self.em)[0]
        self.assertEquals(rec.address, 'grisel@peña.com')
        self.assertEquals(rec.name, 'Grisel Peña')
        self.assertEquals(rec.domain, 'peña.com')

    def test_add_tos(self):
        """
        Lists must also work, of course.
        """
        self.em.add_tos(['marco@polo.com', 'Meat Chicken <meat@chicken.com>'])

        self.assertEquals(len(self.em.to), 2)
        self.assertEquals(EmailRecipient.objects.filter(email=self.em, type=EmailRecipient.TO).count(), 2)

    def test_add_ccs(self):
        """
        Similar to above, but CCs.
        """
        self.em.add_ccs(['marco@polo.com', 'Meat Chicken <meat@chicken.com>'])

        self.assertEquals(len(self.em.cc), 2)
        self.assertEquals(EmailRecipient.objects.filter(email=self.em, type=EmailRecipient.CC).count(), 2)

    def test_add_bccs(self):
        """
        Similar to above, but BCCs.
        """
        self.em.add_bccs(['marco@polo.com', 'Meat Chicken <meat@chicken.com>'])

        self.assertEquals(len(self.em.bcc), 2)
        self.assertEquals(EmailRecipient.objects.filter(email=self.em, type=EmailRecipient.BCC).count(), 2)

    def test_custom_create(self):
        """
        Tests custom manager function
        """
        em = Email.objects.create(**{
            'type': models.WelcomeEmail.get_content_type(),
            'html_body': "<p>Hi</p>",
            'to': {
                'to': 'marco@polo.com',
                'cc': ['Freddy Kruger <freddy@kruger.com>', 'meat@chicken.com']
            }
        })

        self.assertEquals(EmailRecipient.objects.filter(email=em).count(), 3)


class SomeSendable(EmailSendable):
    class Meta:
        abstract = True

    def get_raw_subject(self):
        return 'Whatever'


class EmailSetUpTester(TestCase):
    """
    Makes sure Sendables have the controls over their Transports that
    I think they have.
    """

    def setUp(self):
        self.backend_path = 'django.core.mail.backends.console.EmailBackend'
        self.assertEquals(EmailBackend.objects.all().count(), 0)
        self.ss = SomeSendable()

    def test_initial_backend_by_path(self):
        initial_data = Email.extra_transport_data(self.ss, backend=self.backend_path)
        self.assertIn('backend', initial_data.keys())

        # The above line should have created an EmailBackend record
        self.assertEquals(EmailBackend.objects.all().count(), 1)
        self.assertEquals(EmailBackend.objects.first().path, self.backend_path)

    def test_initial_backend_by_ref(self):
        backend = EmailBackend.objects.create(name='Console',
            path=self.backend_path)

        initial_data = Email.extra_transport_data(self.ss, backend=backend)
        self.assertIn('backend', initial_data.keys())

        # The above line should have created an EmailBackend record
        self.assertEquals(EmailBackend.objects.all().count(), 1)
        self.assertEquals(EmailBackend.objects.first().path, self.backend_path)

    def test_initial_backend_by_id(self):
        backend = EmailBackend.objects.create(name='Console',
            path=self.backend_path)

        initial_data = Email.extra_transport_data(self.ss, backend_id=backend.pk)
        self.assertIn('backend_id', initial_data.keys())

        # The above line should have created an EmailBackend record
        self.assertEquals(EmailBackend.objects.all().count(), 1)
        self.assertEquals(EmailBackend.objects.first().path, self.backend_path)

    def test_add_variable(self):
        em = Email.objects.create(type=models.WelcomeEmail.get_content_type())
        email_var = em.add_variable('some_key', 'some variable')

        self.assertEquals(EmailVariable.objects.filter(email=em).count(), 1)
        self.assertEquals(EmailVariable.objects.last().pk, email_var.pk)


# TODO: Break this out of `django-grapevine` proper and into its
# own extension
if sendgrid:
    class SendGridBackendTester(TestCase):
        """
        The SendGrid EMAIL_BACKEND provides a Django-friendly wrapper
        around the raw SendGrid python library.
        """

        def setUp(self):
            self.email = Email.objects.create(
                type=models.WelcomeEmail.get_content_type(),
                subject="LONG TIME NO SEE LOL",
                html_body="<p>What up homeslice?</p>",
                from_email="homeboy@gmail.com",
                reply_to="homeboy@gmail.com",
                # This line is of particular import
                backend="grapevine.emails.backends.SendGridEmailBackend",
                to={
                    'to': ['marco@polo.com'],
                    'cc': ['Meat Chicken <meat@chicken.com>', 'Denard Robinson <denardr@umich.edu>'],
                    'bcc': 'The NSA <alerts@nsa.gov>'  # Haha, suckas
                }
            )
            self.email.add_variable('should_show_unsubscribe_link', 0)

        def test_message_building(self):
            """
            Make sure the SendGrid EMAIL_BACKEND builds a complete message.
            """
            message = self.email.backend.as_message(self.email)

            # to and ccs get merged into the same list, with SendGrid
            self.assertEquals(len(message.to), 3)
            # The NSA is BCC, not regular to
            self.assertNotIn('NSA', str(message.to))

            # The UUID should be passed as unique arg
            self.assertIn(self.email.guid, message.smtpapi.data['unique_args'].values())

            # Should have removed the unsubscribe link
            self.assertEquals(message.smtpapi.data['filters']['subscriptiontrack']['settings']['enabled'], 0)


class UnsubscribedTester(TestCase):
    """
    This test counts for native Django backends as well as the
    SendGridEmailBackend, because the two ends share a recipient
    storage scheme
    """

    def setUp(self):
        UnsubscribedAddress.objects.create(address='leaveme@alone.com')
        UnsubscribedAddress.objects.create(address='srsly@leavemealone.com')

        self.mixed_recipients = {
            'to': ['miguel@polio.com', 'leaveme@alone.com', 'Leave MeAlone <leaveme@alone.com>'],
            'cc': ['Meat Chicken <meat@chicken.com>', 'Denard Robinson <denardr@umich.edu>'],
            'bcc': ['srsly@leavemealone.com', 'you@canemailme.com'],
        }
        self.single_all_unsubscribed_recipients = ['leaveme@alone.com']
        self.multiple_all_unsubscribed_recipients = ['leaveme@alone.com', 'Marco Polo <srsly@leavemealone.com>']

        self.assertEquals(SendGridEmailFactory().backend.path, 'grapevine.emails.backends.SendGridEmailBackend')

        grapevine_settings.DEBUG = False

    def test_standard_email(self):
        email = EmailFactory()
        email.add_recipients = email.add_recipients(self.mixed_recipients)

        message = email.backend.as_message(email)
        message = email.backend.finalize_message(message)

        self.assertEquals(len(message.to), 1)
        self.assertIn('miguel@polio.com', message.to[0])

        self.assertEquals(len(message.cc), 2)
        self.assertEquals(len(message.bcc), 1)
        self.assertIn('you@canemailme.com', message.bcc[0])

    def test_standard_all_unsubscribed(self):
        self._all_unsubscribed(EmailFactory(), self.single_all_unsubscribed_recipients)
        self._all_unsubscribed(EmailFactory(), self.multiple_all_unsubscribed_recipients)

    def _all_unsubscribed(self, email, recipients):
        email.add_recipients(recipients)

        message = email.backend.as_message(email)
        message = email.backend.finalize_message(message)

        self.assertEquals(len(message.to), 0)

    # TODO: Move this out of `django-grapevine` proper and
    # into its own extension
    if sendgrid:
        def test_sendgrid_email(self):
            email = SendGridEmailFactory()
            email.add_recipients = email.add_recipients(self.mixed_recipients)

            message = email.backend.as_message(email)
            message = email.backend.finalize_message(message)

            self.assertEquals(len(message.to), 3)
            self.assertIn('miguel@polio.com', message.to[0])

            self.assertEquals(len(message.bcc), 1)
            self.assertIn('you@canemailme.com', message.bcc[0])

        def test_sendgrid_all_unsubscribed(self):
            self._all_unsubscribed(SendGridEmailFactory(), self.single_all_unsubscribed_recipients)
            self._all_unsubscribed(SendGridEmailFactory(), self.multiple_all_unsubscribed_recipients)

        def test_webhook_acceptor(self):
            payload = '{"category":["category1","category2","category3"], "unique_args":{"uid":"123456", "purchase":"PO1452297845", "id":"001"}}'

            url = reverse('grapevine:sendgrid-events-webhook')

            resp = self.client.post(url, data=payload, content_type="application/json")
            self.assertEquals(resp.status_code, 200)

            self.assertEquals(RawEvent.objects.first().payload, payload)


@override_settings(EMAIL_BACKEND='django.core.mail.backends.dummy.EmailBackend')
class GrapevineSenderTester(TestCase):
    """
    Testing Grapevine's abstract classes require real classes with real DB tables.
    Thus, the unit tests for its actual message delivery code must live elsewhere.
    """

    def setUp(self):
        super(GrapevineSenderTester, self).setUp()

        self.user = get_user_model().objects.create(username="asadf", email="asdf@asdf.com")
        self.welcome_email = models.WelcomeEmail.objects.create(user=self.user)
        # Alias
        self.sendable = self.welcome_email

        from grapevine.sender import ScheduledSendableSender
        self.sender = ScheduledSendableSender()
        self.assertEquals(models.WelcomeEmail.objects.is_eligible().count(), 1)

    def test_sent_are_ineligible(self):
        """
        Verifies that sent messages are ineligible for resending.
        """
        # Send an email
        self.sendable.send()
        # And now the sendable must be considered ineligible
        self.assertEquals(models.WelcomeEmail.objects.is_eligible().count(), 0)

    def test_queued_are_ineligible(self):
        """
        Verifies that queued messages are ineligible for sending (other than
        by their queued job, of course).
        """
        self.sendable.denote_as_queued()
        # And now the sendable must be considered ineligible
        self.assertEquals(models.WelcomeEmail.objects.is_eligible().count(), 0)

    def test_future_messages_are_ineligible(self):
        """
        Verifies that queued messages are ineligible for sending (other than
        by their queued job, of course).
        """
        self.sendable.scheduled_send_time = (timezone.now() + datetime.timedelta(hours=1))
        self.sendable.save()
        # And now the sendable must be considered ineligible
        self.assertEquals(models.WelcomeEmail.objects.is_eligible().count(), 0)

    def test_base_send(self):
        """
        Individual models are able to able to opt-out of being sent according
        to arbitrary business logic. Make sure that's happening.
        """
        # It should have found > 0 sendable models and sent 1 item
        num_sent, num_sendables = self.sender.deliver_messages()
        self.assertEquals(num_sent, 1)
        self.assertTrue(num_sendables > 0)

    def test_final_check(self):
        """
        Individual models are able to able to opt-out of being sent according
        to arbitrary business logic. Make sure that's happening.
        """
        # Attaching this story will trigger the individual record
        # level send-time opt-out
        self.user.email = ''
        self.user.save()

        # It should have found > 0 sendable models, but sent 0 items
        num_sent, num_sendables = self.sender.deliver_messages()
        self.assertEquals(num_sent, 0)
        self.assertTrue(num_sendables > 0)

        # Our sendable's ``cancelled_at_send_time`` flag should have been set
        self.sendable = models.WelcomeEmail.objects.get(pk=self.sendable.pk)
        self.assertTrue(self.sendable.cancelled_at_send_time)


@override_settings(EMAIL_BACKEND="grapevine.emails.backends.MailGunEmailBackend")
class MailgunTester(TestCase):

    def test_base_send(self):
        user = UserFactory()
        we = models.WelcomeEmail.objects.create(user=user)

        with mock.patch.object(MailGunEmailBackend, 'post') as mocked_post:
            # Fake a response
            mocked_response = requests.Response()
            mocked_response.status_code = 200
            mocked_response._content = {}
            mocked_post.return_value = mocked_response

            is_sent = we.send(backend=settings.EMAIL_BACKEND)
        self.assertTrue(is_sent)

        self.assertEquals(we.message_id, 1)
        self.assertEquals(Email.objects.get(pk=1).status, Email.SENT)

    def test_prepare_data(self):
        email_message = EmailMultiAlternatives(
            subject="Hello old friend!",
            body="Seriously, long time no see.",
            from_email="Marco Polo <marco@polo.com>",
            to=["meat@chicken.com"],
            cc=[],
            bcc=["Top Secret <top@secret.com>", "Top Secret2 <top@secret2.com>"],
            headers={},
        )
        email_message._email = Email().ensure_guid()

        data = MailGunEmailBackend().prepare_data(email_message)

        self.assertEquals(data["to"], "meat@chicken.com")
        self.assertNotIn("cc", data.keys())
        self.assertEquals(data["bcc"], "Top Secret <top@secret.com>, Top Secret2 <top@secret2.com>")
        self.assertEquals(data["from"], email_message.from_email)

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

# Django
from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.utils import override_settings

# 3rd Party
from grapevine.generics import EmailSendable
from grapevine.settings import grapevine_settings
from grapevine.emails.models import Email, EmailRecipient, \
    EmailBackend, EmailVariable, UnsubscribedAddress, RawEvent

# Local Apps
from core import models
from factories import EmailFactory, SendGridEmailFactory


class RecipientsTester(TestCase):
    """
    Tests all things Recipient-setting related.
    """

    def setUp(self):
        self.em = Email.objects.create(type=models.WelcomeEmail.content_type())

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
            'type': models.WelcomeEmail.content_type(),
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
        initial_data = Email.finish_initial_data(self.ss, {}, backend=self.backend_path)
        self.assertIn('backend', initial_data.keys())

        # The above line should have created an EmailBackend record
        self.assertEquals(EmailBackend.objects.all().count(), 1)
        self.assertEquals(EmailBackend.objects.first().path, self.backend_path)

    def test_initial_backend_by_ref(self):
        backend = EmailBackend.objects.create(name='Console',
            path=self.backend_path)

        initial_data = Email.finish_initial_data(self.ss, {}, backend=backend)
        self.assertIn('backend', initial_data.keys())

        # The above line should have created an EmailBackend record
        self.assertEquals(EmailBackend.objects.all().count(), 1)
        self.assertEquals(EmailBackend.objects.first().path, self.backend_path)

    def test_initial_backend_by_id(self):
        backend = EmailBackend.objects.create(name='Console',
            path=self.backend_path)

        initial_data = Email.finish_initial_data(self.ss, {}, backend_id=backend.pk)
        self.assertIn('backend_id', initial_data.keys())

        # The above line should have created an EmailBackend record
        self.assertEquals(EmailBackend.objects.all().count(), 1)
        self.assertEquals(EmailBackend.objects.first().path, self.backend_path)

    def test_add_variable(self):
        em = Email.objects.create(type=models.WelcomeEmail.content_type())
        email_var = em.add_variable('some_key', 'some variable')

        self.assertEquals(EmailVariable.objects.filter(email=em).count(), 1)
        self.assertEquals(EmailVariable.objects.last().pk, email_var.pk)


class SendGridBackendTester(TestCase):
    """
    The SendGrid EMAIL_BACKEND provides a Django-friendly wrapper
    around the raw SendGrid python library.
    """

    def setUp(self):
        self.email = Email.objects.create(
            type=models.WelcomeEmail.content_type(),
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
        self.assertEquals(len(message.data['to']), 3)
        # The NSA is BCC, not regular to
        self.assertNotIn('NSA', str(message.data['to']))

        # The UUID should be passed as unique arg
        self.assertIn(self.email.guid, message.data['unique_args'].values())

        # Should have removed the unsubscribe link
        self.assertEquals(message.data['filters']['subscriptiontrack']['settings']['enabled'], 0)


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

    def test_sendgrid_email(self):
        email = SendGridEmailFactory()
        email.add_recipients = email.add_recipients(self.mixed_recipients)

        message = email.backend.as_message(email)
        message = email.backend.finalize_message(message)

        self.assertEquals(len(message.to), 3)
        self.assertIn('miguel@polio.com', message.to[0])

        self.assertEquals(len(message.bcc), 1)
        self.assertIn('you@canemailme.com', message.bcc[0])

    def test_standard_all_unsubscribed(self):
        self._all_unsubscribed(EmailFactory(), self.single_all_unsubscribed_recipients)
        self._all_unsubscribed(EmailFactory(), self.multiple_all_unsubscribed_recipients)

    def test_sendgrid_all_unsubscribed(self):
        self._all_unsubscribed(SendGridEmailFactory(), self.single_all_unsubscribed_recipients)
        self._all_unsubscribed(SendGridEmailFactory(), self.multiple_all_unsubscribed_recipients)

    def _all_unsubscribed(self, email, recipients):
        email.add_recipients(recipients)

        message = email.backend.as_message(email)
        message = email.backend.finalize_message(message)

        self.assertEquals(len(message.to), 0)

    def test_webhook_acceptor(self):
        payload = '{"category":["category1","category2","category3"], "unique_args":{"uid":"123456", "purchase":"PO1452297845", "id":"001"}}'

        url = reverse('grapevine:sendgrid-events-webhook')

        resp = self.client.post(url, data=payload, content_type="application/json")
        self.assertEquals(resp.status_code, 200)

        self.assertEquals(RawEvent.objects.first().payload, payload)


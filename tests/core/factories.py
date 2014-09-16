from __future__ import unicode_literals

# 3rd Party
import factory
# from factory import fuzzy
from grapevine.emails import models


class EmailFactory(factory.django.DjangoModelFactory):
    FACTORY_FOR = models.Email

    html_body = "<p>Hello, world.</p>"
    subject = "Marco"


class SendGridEmailFactory(EmailFactory):
    backend = 'grapevine.emails.backends.SendGridEmailBackend'

from __future__ import unicode_literals

# Django
from django.contrib.auth import get_user_model

# 3rd Party
import factory
from factory import fuzzy
from grapevine.emails import models


class UserFactory(factory.django.DjangoModelFactory):
    username = factory.fuzzy.FuzzyText(length=10)
    first_name = factory.fuzzy.FuzzyText(length=10)
    last_name = factory.fuzzy.FuzzyText(length=10)
    email = factory.LazyAttribute(lambda a: '{0}.{1}@gmail.com'.format(a.first_name, a.last_name).lower())

    class Meta:
        model = get_user_model()


class EmailFactory(factory.django.DjangoModelFactory):
    html_body = "<p>Hello, world.</p>"
    subject = "Marco"

    class Meta:
        model = models.Email


class SendGridEmailFactory(EmailFactory):
    backend = 'grapevine.emails.backends.SendGridEmailBackend'

    class Meta:
        model = models.Email


class MailGunEmailFactory(EmailFactory):
    backend = 'grapevine.emails.backends.MailGunEmailFactory'

    class Meta:
        model = models.Email

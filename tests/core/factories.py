from __future__ import unicode_literals

# Django
from django.contrib.auth import get_user_model

# 3rd Party
import factory
from factory import fuzzy
from grapevine.emails import models

# Local Apps
from .models import WelcomeEmail


class UserFactory(factory.django.DjangoModelFactory):
    FACTORY_FOR = get_user_model()

    username = factory.fuzzy.FuzzyText(length=10)
    first_name = factory.fuzzy.FuzzyText(length=10)
    last_name = factory.fuzzy.FuzzyText(length=10)
    email = factory.LazyAttribute(lambda a: '{0}.{1}@gmail.com'.format(a.first_name, a.last_name).lower())


class WelcomeEmailFactory(factory.django.DjangoModelFactory):
    FACTORY_FOR = WelcomeEmail


class EmailFactory(factory.django.DjangoModelFactory):
    FACTORY_FOR = models.Email

    html_body = "<p>Hello, world.</p>"
    subject = "Marco"


class SendGridEmailFactory(EmailFactory):
    backend = 'grapevine.emails.backends.SendGridEmailBackend'


class MailGunEmailFactory(EmailFactory):
    backend = 'grapevine.emails.backends.MailGunEmailFactory'

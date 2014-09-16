from __future__ import unicode_literals

# 3rd Party
import factory
from factory import fuzzy

# Local Apps
from models import HipChat

class HipChatFactory(factory.django.DjangoModelFactory):
    FACTORY_FOR = HipChat

    from_name = factory.fuzzy.FuzzyText(length=15)
    message = factory.fuzzy.FuzzyText(length=255)

class NotifyingHipChatFactory(HipChatFactory):
    should_notify = HipChat.YES

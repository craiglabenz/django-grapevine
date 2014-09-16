# -*- coding: utf-8 -*-
from __future__ import unicode_literals

# Django
from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase

# Local Apps
import factories
from grapevine.settings import grapevine_settings
from grapevine.hipchat.models import HipChat

# SocialProof (will have to change to demo app when this is
#    pulled out of our codebase and put into PIP)
from stories import models as story_models


class HipChatTester(TestCase):
    def setUp(self):
        self.chat_message = HipChat.objects.create()

    def test_message_formats(self):
        hipchat = factories.HipChatFactory()

        message = "<p>Aenean eu leo quam. Pellentesque ornare sem lacinia <i>quam</i> venenatis vestibulum. <strong><i>Integer</i></strong> posuere erat a ante venenatis dapibus posuere velit aliquet.</p>"
        hipchat.message = message

        # default is HTML
        self.assertEquals(hipchat.message_format, HipChat.FORMAT_HTML)
        self.assertEquals(hipchat.message, message)

        # switch it over to text format
        hipchat.message_format = HipChat.FORMAT_TEXT
        self.assertEquals(hipchat.message_format, HipChat.FORMAT_TEXT)
        self.assertEquals(hipchat.message, "Aenean eu leo quam. Pellentesque ornare sem lacinia quam venenatis vestibulum. Integer posuere erat a ante venenatis dapibus posuere velit aliquet.")

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

# Django
from django.test import TestCase

# Local Apps
from grapevine.models import Transport, QueuedMessage


class TransportTester(TestCase):

    def setUp(self):
        self.tp = Transport()

    def test_html_to_text(self):
        """
        HTML bodies should be converted to their markdown-y plaintext alternatives.
        """
        self.tp.html_body = '<p>Hello, old friend. Click <a href="http://www.google.com">here</a>.</p>'
        self.tp.determine_text_body()
        self.assertEquals(self.tp.text_body, 'Hello, old friend. Click [here](http://www.google.com).\n\n')

    def test_html_to_text_with_special_characters(self):
        """
        Non-ascii characters shouldn't cause a conniption.
        """
        self.tp.html_body = '<p>Peña</p>'
        self.tp.determine_text_body()
        self.assertEquals(self.tp.text_body, 'Peña\n\n')

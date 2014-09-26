# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import copy

# Django
from django.conf import settings
from django.test import TestCase
from django.test.utils import override_settings

# 3rd Party
import grapevine


class GrapevineSettingsTester(TestCase):

    def prepare_settings(self, **kwargs):
        """
        Can't be ``setUp()`` because local function ``override_settings`` calls
        would not be honored. We have to pass in the global django settings module
        here, and it needs to be whatever we doctored with ``override_settings``.
        """
        # Merge custom GRAPEVINE settings with what's defined in the settings file
        user_gv_settings = copy.copy(settings.GRAPEVINE)
        user_gv_settings.update(kwargs)

        self.grapevine_settings = grapevine.settings.GrapevineSettings(
            user_settings=user_gv_settings,
            defaults=grapevine.settings.DEFAULTS,
            global_settings_keys=grapevine.settings.GLOBAL_DEFAULTS,
            importable_settings=grapevine.settings.IMPORTABLE_SETTINGS,
            django_settings=settings
        )

    @override_settings(EMAIL_BACKEND='grapevine.emails.backends.MailGunEmailBackend', GRAPEVINE={})
    def test_backend(self):
        EMAIL_BACKEND = 'grapevine.emails.backends.MailGunEmailBackend'

        self.prepare_settings(EMAIL_BACKEND=EMAIL_BACKEND)
        self.assertEquals(settings.EMAIL_BACKEND, EMAIL_BACKEND)
        self.assertEquals(settings.GRAPEVINE, {})

        self.assertEquals(self.grapevine_settings.EMAIL_BACKEND, EMAIL_BACKEND)

    @override_settings(DEBUG=True)
    def test_django_debug_true(self):
        self.prepare_settings()
        self.assertTrue(self.grapevine_settings.DEBUG)

    @override_settings(DEBUG=False, GRAPEVINE={})
    def test_django_debug_false(self):
        self.prepare_settings()
        self.assertFalse(self.grapevine_settings.DEBUG)

    def test_grapevine_debug_true(self):
        self.prepare_settings(DEBUG=True)
        self.assertTrue(self.grapevine_settings.DEBUG)

    def test_grapevine_debug_false(self):
        self.prepare_settings(DEBUG=False)
        self.assertFalse(self.grapevine_settings.DEBUG)



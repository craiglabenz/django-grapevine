"""
Grapevine settings are namespaced in the GRAPEVINE setting.
For example, your project's `settings.py` file might look like this:

GRAPEVINE = {
    'EMAIL_BACKEND' = 'grapevine.emails.backends.SendGridEmailBackend',
}

**Nod to Django Rest Framework's structured settings setup.**
"""
from __future__ import unicode_literals

# Django
from django.conf import settings
from django.utils import importlib, six


USER_SETTINGS = getattr(settings, 'GRAPEVINE', {})
DEFAULTS = {
    'SENDER_CLASS': 'grapevine.engines.SynchronousSender',
    'EMAIL_BACKEND': None,
    'DEBUG_EMAIL_ADDRESS': 'test@email.com',
}

# These values, if unspecified, fallback to their
# global settings values
GLOBAL_DEFAULTS = (
    'EMAIL_BACKEND',
    'DEBUG',
)

# List of settings that will be dotted import paths
IMPORTABLE_SETTINGS = (
    'SENDER_CLASS',
)


def perform_import(val, setting_name):
    """
    If the given setting is a string import notation,
    then perform the necessary import or imports.
    """
    if isinstance(val, six.string_types):
        return import_from_string(val, setting_name)
    elif isinstance(val, (list, tuple)):
        return [import_from_string(item, setting_name) for item in val]
    return val


def import_from_string(val, setting_name):
    """
    Attempt to import a class from a string representation.
    """
    try:
        # Nod to tastypie's use of importlib.
        parts = val.split('.')
        module_path, class_name = '.'.join(parts[:-1]), parts[-1]
        module = importlib.import_module(module_path)
        return getattr(module, class_name)
    except ImportError as e:
        msg = "Could not import '%s' for API setting '%s'. %s: %s." % (val, setting_name, e.__class__.__name__, e)
        raise ImportError(msg)


class GrapevineSettings(object):
    """
    A settings object that allows Grapevine to access user-specified settings
    values, with appropriate default fallbacks.

        from grapevine.settings import grapevine_settings
        if grapevine_settings.DEBUG:
            # Do stuff
        else:
            # Do other stuff
    """

    def __init__(self, user_settings=None, defaults=None,
                 global_settings_keys=None, importable_settings=None, django_settings=None):
        self.user_settings = user_settings or {}
        self.defaults = defaults or {}
        self.global_settings_keys = global_settings_keys or {}
        self.importable_settings = importable_settings or ()
        self.django_settings = django_settings or settings

    def __getattr__(self, attr):
        if attr not in self.defaults.keys() and attr not in self.global_settings_keys:
            raise AttributeError("Invalid Grapevine setting: '%s'" % (attr,))

        try:
            # First try user settings
            val = self.user_settings[attr]
        except KeyError:
            # Fall back to defaults
            val = self.defaults.get(attr, None)

        # Fallback to global settings if appropriate
        if val is None and attr in self.global_settings_keys:
            val = getattr(settings, attr, None)

        # Coerce import strings into classes
        if val and attr in self.importable_settings:
            val = perform_import(val, attr)

        # Cache the result
        setattr(self, attr, val)
        return val

grapevine_settings = GrapevineSettings(USER_SETTINGS, DEFAULTS, GLOBAL_DEFAULTS, IMPORTABLE_SETTINGS)

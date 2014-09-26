from __future__ import unicode_literals

import os
SETTINGS_DIR = os.path.dirname(__file__)
BASE_DIR = os.path.dirname(os.path.dirname(SETTINGS_DIR))


INSTALLED_APPS = [
    'suit',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',

    # Used for database templates
    'tablets',
    'grapevine',
    'grapevine.emails',

    # Houses some basic stuff
    'core',
]

######## GRAPEVINE CONFIGURATION
GRAPEVINE = {
    'DEBUG': True,
    'DEBUG_EMAIL_ADDRESS': 'test@djangograpevine.com',
    'SENDER_CLASS': 'grapevine.engines.SynchronousSender',
}
######## END GRAPEVINE CONFIGURATION


######## EMAIL CONFIGURATION
# See: https://docs.djangoproject.com/en/stable/ref/settings/#email-backend
# EMAIL_BACKEND = 'grapevine.emails.backends.SendGridEmailBackend'
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Individual message constants
DEFAULT_FROM_EMAIL = 'Craig Labenz <admins@djangograpevine.com>'
DEFAULT_REPLY_TO = 'help@djangograpevine.com'
DEFAULT_SUBJECT = 'Hello from Grapevine!'
######## END EMAIL CONFIGURATION


######## TEMPLATES CONFIG
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    'tablets.loaders.DatabaseLoader',
)
TEMPLATE_DIRS = (
    BASE_DIR + '/grapevine',
)
######## END TEMPLATES CONFIG


######## SENDGRID CONFIGURATION
SENDGRID_USERNAME = "username-would-go-here"
SENDGRID_PASSWORD = "password-would-go-here"
######## END SENDGRID CONFIGURATION


######## MAILGUN CONFIGURATION
# As per: http://documentation.mailgun.com/user_manual.html#sending-via-api
MAILGUN_ACCESS_KEY = 'key-3ax6xnjp29jd6fds4gc373sgvjxteol0'
MAILGUN_SERVER_NAME = 'samples.mailgun.org'
######## END MAILGUN CONFIGURATION


TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.core.context_processors.request",
    "django.core.context_processors.tz",
    "django.contrib.messages.context_processors.messages",
    "core.context_processors.settings",
)


TEST_RUNNER = "django.test.runner.DiscoverRunner"

SITE_ID = 1

ROOT_URLCONF = "urls"

DEBUG = True

STATIC_URL = '/static/'

SECRET_KEY = 'whatever man these are tests'

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(os.path.dirname(__file__), 'database.db'),
    }
}

import sys
sys.dont_write_bytecode = True

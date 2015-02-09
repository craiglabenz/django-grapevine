from __future__ import unicode_literals

# Local Apps
from .jobs import async_process_events


default_app_config = 'grapevine.emails.apps.EmailsConfig'


def send_mail(subject, message, from_email, recipient_list, html_message='',
            fail_silently=False, auth_user=None, auth_password=None,
            connection=None):
    """
    Overrides Django's native ``send_mail`` function to add standard Grapevine
    functionality like unsubscribe honoring and DEBUG mode sending.
    """
    from . import models

    email = models.Email.objects.create(
        subject=subject,
        html_body=html_message,
        text_body=message,
        from_email=from_email,
        to=recipient_list,
    )

    return email.send()

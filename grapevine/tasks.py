from __future__ import unicode_literals

from .sender import ScheduledSendableSender

try:
    from celery import shared_task

    @shared_task
    def async_deliver_messages():
        ScheduledSendableSender().deliver_messages()

except ImportError:
    # No celery? No worries, just no async for you.
    pass
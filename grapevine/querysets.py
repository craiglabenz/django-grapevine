from __future__ import unicode_literals

# Django
from django.utils import timezone
from django.db.models.query import QuerySet

# Local Apps
from . import models


class SendableQuerySet(QuerySet):

    def sent(self):
        return self.exclude(message_id=None)

    def unsent(self):
        return self.filter(message_id=None, cancelled_at_send_time=False)

    def ready_to_send(self):
        return self.filter(scheduled_send_time__lte=timezone.now())

    def not_queued(self):
        message_ids = models.QueuedMessage.objects.\
            filter(message_type=self.model.get_content_type()).\
            values_list('message_id', flat=True)

        return self.exclude(pk__in=message_ids)

    def is_sendable(self):
        """
        Override hook for child querysets to amend logic to remove
        scheduled emails that have since become obselete.
        """
        return self

    def is_eligible(self):
        return self.unsent().ready_to_send().not_queued().is_sendable()

    def with_messages(self, should_preload_events=True):
        """
        Alert: Evaluates the queryset and attaches the ``_message`` attr!
        **DOES NOT SUPPORT CHAINING**
        """
        objs = []

        # Email, HipChat, whatever, just load the relevant class
        transport_class = self.model.get_transport_class()

        # Distill the message_ids as a map back to their objs
        message_id_map = {}
        for obj in self:
            message_id_map[obj.message_id] = obj
            objs.append(obj)

        # Load all relevant messages
        messages = transport_class._default_manager.filter(pk__in=message_id_map.keys())

        if should_preload_events and hasattr(transport_class, "events"):
            messages = messages.prefetch_related("events")

        for message in messages:
            message_id_map[message.pk]._message = message

        return objs

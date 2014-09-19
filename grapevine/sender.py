from __future__ import unicode_literals

# Django
from django.contrib.contenttypes.models import ContentType

# 3rd Party
# from celery import shared_task

# Local Apps
from grapevine.settings import grapevine_settings


class ScheduledSendableSender(object):
    """
    Loops over all ContentTypes and sends each eligible message
    that extend SendableMixin.
    """
    def __init__(self):
        pass

    @staticmethod
    # @shared_task(queue="sendable_queuer")
    def async_deliver_messages():
        sender = ScheduledSendableSender()
        return sender.deliver_messages()

    def deliver_messages(self):
        from grapevine import mixins

        # self.get_logger().info("Beginning scan for sendable messages...")

        num_sent = num_sendables = 0
        content_types = [ct for ct in ContentType.objects.all()]
        for content_type in content_types:
            cls = content_type.model_class()

            # Stale content types will return ``None``
            # above, so make sure to skip such results
            if not cls:
                continue

            if issubclass(cls, mixins.SendableMixin):
                num_sendables += 1
                num_sent += ScheduledSendableSender.process_sendable_model(cls)

        # self.get_logger().info("Sent %s messages for %s total Sendable models.", num_sent, num_sendables)

        return num_sent, num_sendables

    @staticmethod
    def process_sendable_model(cls):
        """
        Arguments:
        cls     {mixed}     A non-abstract Django model that extends one of
                            Grapevine's SendableMixin classes.
        """
        # Create a single instance of the class that actually pushes
        # the Sendable's ``send`` button, or queues up that pushing
        sender = grapevine_settings.SENDER_CLASS()

        # Loop over all unsent, but eligible
        num_sent = 0
        sendable_objs = [obj for obj in ScheduledSendableSender.all_eligible_by_sendable(cls)]
        for sendable_obj in sendable_objs:
            # Some objects may have been scheduled for a long time and
            # require an individual check before sending that would be
            # too expensive to place into ``all_eligible()``.
            should_send = sendable_obj.confirm_individual_sendability()
            if should_send:
                is_sent = sender.send(sendable_obj)
                if is_sent:
                    num_sent += 1
        return num_sent

    @staticmethod
    def all_eligible_by_sendable(cls):
        """
        Component of `process_sendable` broken out for testing purposes.
        """
        return cls.objects.is_eligible()

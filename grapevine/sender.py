from __future__ import unicode_literals

# Local Apps
from grapevine.settings import grapevine_settings
from grapevine.utils import valid_content_types


class ScheduledSendableSender(object):
    """
    Loops over all ContentTypes and sends each eligible message
    that extend SendableMixin.
    """
    def __init__(self):
        pass

    def deliver_messages(self):
        from grapevine import mixins

        # self.get_logger().info("Beginning scan for sendable messages...")

        num_sent = num_sendables = 0

        # Stale content types will return ``None`` when looping
        # over the CT table, so use this helper function to remove
        # stale Content Types
        for content_type in valid_content_types():
            content_type_cls = content_type.model_class()

            if issubclass(content_type_cls, mixins.SendableMixin):
                num_sendables += 1
                num_sent += ScheduledSendableSender.process_sendable_model(content_type_cls)

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
        sendable_objs = [obj for obj in cls.objects.is_eligible()]
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

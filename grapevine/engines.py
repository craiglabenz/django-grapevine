from __future__ import unicode_literals


class SynchronousSender(object):

    def send(self, sendable, *args, **kwargs):
        """
        Puts bits directly on the wire.
        """
        # self.get_logger().info("Synchronously sending %s:%s", sendable.__class__.__name__, sendable.pk)
        return sendable.send(*args, **kwargs)


class AsynchronousSender(object):

    def send(self, sendable, *args, **kwargs):
        """
        Pass sendable PK to a queue.
        """
        # self.get_logger().info("Asynchronously sending %s:%s", sendable.__class__.__name__, sendable.pk)
        sendable.denote_as_queued()
        return sendable.async_send.delay(sendable.__class__, sendable.pk, *args, **kwargs)

from __future__ import unicode_literals

# Django
from django.core.management.base import BaseCommand, CommandError

# Local Apps
from grapevine.sender import ScheduledSendableSender


class Command(BaseCommand):
    help = "Sends or queues all eligible Messages"

    def handle(self, *args, **options):
        sender = ScheduledSendableSender()
        num_sent, num_sendables = sender.deliver_messages()
        self.stdout.write("Sent %s messages from %s total Sendable models." % (num_sent, num_sendables,))

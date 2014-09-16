from __future__ import unicode_literals

# Django
from django.db import models

# Local Apps
from grapevine.emails.utils import parse_email


class EmailManager(models.Manager):

    def create(self, **kwargs):
        """
        Takes and appropriately processes the extra keyword args:
            `recipients` and `{backend|backend_id}`
        """
        recipients = kwargs.pop('to', None)

        key, backend = self.model.determine_backend(**kwargs)
        if backend:
            # If we matched a backend, great
            kwargs[key] = backend

        obj = super(EmailManager, self).create(**kwargs)

        if recipients:
            obj.add_recipients(recipients)

        return obj


class EmailRecipientManager(models.Manager):

    def create(self, **kwargs):
        """
        Handles normal `create` duties, plus some additional "address" parsing
        """
        address = kwargs.get('address', '')
        name, address = parse_email(address)
        kwargs["name"] = name
        kwargs["address"] = address

        return super(EmailRecipientManager, self).create(**kwargs)

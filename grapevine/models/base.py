from __future__ import unicode_literals
import json

# Django
from django.db import models, transaction
from django.core.urlresolvers import reverse
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone


class GrapevineModel(models.Model):

    # Bookkeeping
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    @property
    def meta_info(self):
        return (self._meta.app_label, self._meta.model_name,)

    @property
    def admin_view_info(self):
        return '%s_%s' % self.meta_info

    @property
    def admin_uri(self):
        return reverse('admin:%s_%s_change' % (self._meta.app_label, self._meta.model_name,), args=(self.pk,))

    @classmethod
    def get_content_type(cls):
        return ContentType.objects.get_for_model(cls)

    @classmethod
    def field_names(cls):
        """
        Returns the names of all fields on the model
        """
        return [field.name for field in cls._meta.fields]

    def finalize_serialization(self, serialized, strip_empty=False):
        """
        A hook for child classes to do more phun stuff.
        """
        if strip_empty:
            for key, value in serialized.items():
                if value is None or (isinstance(value, dict) and value['id'] is None):
                    serialized.pop(key)
        return serialized

    def serialize(self, full=False, id_nested=False, strip_empty=False, excludes=[]):
        """
        Returns a dictionary of all local fields.
        """
        serialized = {field.name: self.get_field_value(field.name, full) for field in self.__class__._meta.fields if field.name not in excludes}
        return self.finalize_serialization(serialized, strip_empty=strip_empty)

    def get_field_value(self, field_name, full=False):
        """
        Returns a given value of for this instantiated model.

        Arguments:
        field_name    {string}      The value of the attr you want
        full          {bool}        OPTIONAL. If the passed name is a relation, should it be hydrated?
                                    Defaults to False.
        """
        field = self._meta.get_field(field_name)
        # Is this a related field or a literal?
        if isinstance(field, models.fields.related.RelatedField):
            if full:
                # It's related and they ordered it hydrated
                val = getattr(self, field_name, None)
                # Pull out the value and hydrate it if it exists, else
                # return None
                if val is not None:
                    return val.field_values()  # Don't forward `full` to avoid cyclical problems
                else:
                    return None
            else:
                # Not hydrated is easy enough, just return the PK we
                # already have on hand
                _id = getattr(self, '%s_id' % (field_name,), None)
                return {'id': _id}
        elif isinstance(field, models.fields.DateField):  # Covers both DateTimeField and DateField
            return self._meta.get_field(field_name).value_to_string(self)
        else:
            # Not related? Too easy.
            return getattr(self, field_name, None)

    def reload(self):
        """
        In place DB update of the record.
        """
        new_self = self.__class__.objects.get(pk=self.pk)
        self.__dict__.update(new_self.__dict__)
        return self

    def append_to_log(self, log, should_save=True, desc=None, should_use_transaction=True,
                      should_reload=True):
        """
        The wrapper function around ``_append_to_log()``. The distinction exists to help
        sanely enforce the ``should_use_transaction`` flag.
        """
        if should_save and should_use_transaction:
            with transaction.atomic():
                return self._append_to_log(log, should_save, desc, should_reload)
        else:
            return self._append_to_log(log, should_save, desc, should_reload)

    def _append_to_log(self, log, should_save=True, desc=None, should_reload=True):
        """
        Does the actual work of formatting a log, optional name, and timestamp into
        a block of text that gets appended to the ``self.log``.
        """
        assert 'log' in self.field_names(), "Cannot call ``append_to_log()`` on \
            model without a field named ``log``."

        if self.log is None:
            self.log = ''
            self.save()

        if isinstance(log, dict):
            log = json.dumps(log)

        if should_reload:
            # Update local data to ensure sure nothing else committed something
            # to this record before we entered this transaction.
            self.reload()

        pre_log = '##################\n'
        pre_log += '%s\n' % timezone.now().strftime('%b %d, %Y, %I:%M:%S %p UTC')
        if desc:
            pre_log += '**%s**\n' % desc

        post_log = '\n##################\n'

        self.log += '%s%s%s' % (pre_log, log, post_log,)
        if should_save:
            self.save()

        return self

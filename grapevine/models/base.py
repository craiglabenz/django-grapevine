from __future__ import unicode_literals
import json

# Django
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.db import models, transaction
from django.utils import timezone


try:
    from termcolor import cprint as _cprint, colored
except ImportError:
    def _cprint(msg, *args, **kwargs):
        print(msg)

    def colored(msg, *args, **kwargs):
        return msg


def cprint(msg, *args, **kwargs):
    if settings.TESTING:
        return

    if settings.DEBUG:
        _cprint(msg, *args, **kwargs)
    else:
        pass


class GrapevineTimeKeepingModel(models.Model):

    # Bookkeeping
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class GrapevineLogicModel(models.Model):

    class Meta:
        abstract = True

    def __unicode__(self):
        '''Python 2.7 friendliess'''
        return self.as_str()

    def __str__(self):
        '''
        Designed to provide a safe fallback for getting a simple
        string representation of a model.

        Written after one too many career experiences with 500ing
        admin pages because a field in the `__str__` method was
        unexpectedly blank.
        '''
        try:
            return self.as_str()
        except Exception as e:
            if settings.DEBUG:
                cprint("__str__ error {}".format(e), color="red")
            return self.as_str_fallback()

    def as_str_fallback(self):
        if self.pk:
            return '{} Id: {}'.format(self._meta.verbose_name, self.pk)
        else:
            return "Unsaved {}".format(self._meta.verbose_name)

    def as_str(self):
        """
        Classes extending BaseModel are encouraged to implement ``as_str``
        instead of ``__str__`` to prevent any accidental data mismatching
        from ever breaking production functionality.
        """
        name = getattr(self, self.AS_STR_FIELD, None)

        if not name:
            getter = getattr(self, 'get_{}'.format(self.AS_STR_FIELD), None)
            if getter:
                name = getter()

        if not name:
            raise ValueError("Could not generate `{}` for {}".format(self.AS_STR_FIELD, self.as_str_fallback()))

        return name

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


class GrapevineModel(GrapevineLogicModel, GrapevineTimeKeepingModel):

    class Meta:
        abstract = True

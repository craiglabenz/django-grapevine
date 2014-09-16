from __future__ import unicode_literals
import datetime

# Django
from django.contrib import admin
from django.utils import timezone


class OnSpecificDateListFilter(admin.FieldListFilter):

    format = 'YYYY-MM-DD'
    endswith = '__date'

    def __init__(self, field, request, params, model, model_admin, field_path):
        super(OnSpecificDateListFilter, self).__init__(field, request, params, model, model_admin, field_path)

    def expected_parameters(self):
        return [self.field_path + self.endswith]

    def lookups(self, request, model_admin):
        return []

    @property
    def qs_value(self):
        return self.field_path + self.endswith

    def choices(self, cl):
        for x in xrange(31):
            date = timezone.now()
            # By default, offer 15 days ago to 15 days from now
            date = date + datetime.timedelta(days=(x - 15))
            values = {
                self.qs_value: '%s-%s-%s' % (date.year, date.month, date.day,)
            }
            yield {
                'selected': self.used_parameters.get(self.qs_value, None) == values[self.qs_value],
                'query_string': cl.get_query_string(values),
                'display': date.strftime('%a %b %d, %Y')
            }

    def queryset(self, request, queryset):
        processed_params = self.process_used_parameters()
        return queryset.filter(**processed_params)

    def process_used_parameters(self):
        """
        Because we accept a querystring value like "my_field__date=2014-01-01",
        which doesn't make sense by itself to the ORM, we have to do some parsing.
        """
        processed_params = {}
        for key, value in self.used_parameters.items():
            if key.endswith(self.endswith):
                # Split into ``field_name`` and "date" on the "__"
                key_field, key_suffix = key.split('__')

                # Split the date, too
                year, month, day = value.split('-')

                processed_params[key_field + '__year'] = int(year)
                processed_params[key_field + '__month'] = int(month)
                processed_params[key_field + '__day'] = int(day)
            else:
                processed_params[key] = value
        return processed_params

# register the filter
admin.filters.FieldListFilter.register(
    lambda f: isinstance(f, (models.DateField, models.DateTimeField,)), OnSpecificDateListFilter)

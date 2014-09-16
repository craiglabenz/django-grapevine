from __future__ import unicode_literals

# Django
from django import forms
from django.contrib.admin.widgets import AdminSplitDateTime

# Local Apps
from tablets.models import Template


class AdminBulkEditForm(forms.Form):

    template = forms.ModelChoiceField(queryset=Template.objects.all(), help_text='Supply a value for this OR the Frozen template.')
    customized_from_email = forms.CharField(label='Frozen From Email')
    customized_reply_to = forms.CharField(label='Frozen Reply To')
    customized_subject = forms.CharField(label='Frozen Subject')
    customized_template = forms.CharField(label='Frozen Template', widget=forms.Textarea, help_text='A value here will trump anything supplied for "Template".')
    scheduled_send_time = forms.DateTimeField(label='Send Time', widget=AdminSplitDateTime)

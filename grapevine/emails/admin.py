from __future__ import unicode_literals

# Django
from django.conf import settings
from django.contrib import admin
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe

# Local Apps
from grapevine.admin.base import BaseModelAdmin, SendableAdminMixin
from .models import Email, EmailRecipient, EmailBackend, EmailVariable, \
    RawEvent, Event, EmailEvent, UnsubscribedAddress

IS_SUIT_AVAILBLE = "suit" in settings.INSTALLED_APPS


class EmailableAdminMixin(SendableAdminMixin):
    """
    Used for Sendables specifically of the Emailable variety.
    """
    # Used for admin display purposes
    message_type_verbose = "Email"
    if IS_SUIT_AVAILBLE:
        change_form_template = 'admin/suit_change_emailable_form.html'
    else:
        change_form_template = 'admin/change_emailable_form.html'

    def get_test_recipient(self, request, obj_id):
        return request.user.email

    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        if obj:
            try:
                context['reply_to'] = obj.get_reply_to()
            except ValueError as e:
                context['error_reply_to'] = "ERROR: %s" % (e.args[0],)
            except NotImplementedError:
                context['error_reply_to'] = "ERROR: Could not generate a `reply_to`. Does this template lack a value?"

            try:
                val = obj.get_from_email()
                val = val.replace("<", "&lt;").replace(">", "&gt;")
                context['from_email'] = mark_safe(val)
            except ValueError as e:
                context['error_from_email'] = "ERROR: %s" % (e.args[0],)
            except NotImplementedError:
                context['error_from_email'] = "ERROR: Could not generate a `from_email`. Does this template lack a value?"

            try:
                context['subject'] = obj.get_subject()
            except ValueError:
                context['error_subject'] = "ERROR: Could not populate everything in \"%s\"" % (obj.get_raw_subject(),)
            except NotImplementedError:
                context['error_subject'] = "ERROR: Could not generate a subject. Does the template lack a subject?"

        return super(EmailableAdminMixin, self).render_change_form(request, context, add, change, form_url, obj)


class EmailInlineMixin(object):
    extra = 0

    def has_add_permission(self, obj):
        return False

    def has_delete_permission(self, request, obj):
        return False


class EmailVariableInline(EmailInlineMixin, admin.TabularInline):
    model = EmailVariable
    readonly_fields = ['key', 'value']
    verbose_name_plural = 'Variables'


class EmailRecipientInline(EmailInlineMixin, admin.TabularInline):
    model = EmailRecipient
    readonly_fields = ['address', 'domain', 'name', 'type']
    verbose_name_plural = 'Recipients'


class EmailEventInline(EmailInlineMixin, admin.TabularInline):
    model = EmailEvent

    def admin_raw_event(self, obj):
        url = reverse('admin:emails_rawevent_change', args=(obj.raw_event.pk,))
        return '<a href="%s">%s</a>' % (url, obj.raw_event.pk,)
    admin_raw_event.short_description = "Raw Event"
    admin_raw_event.allow_tags = True

    readonly_fields = ['event', 'admin_raw_event', 'happened_at']
    fields = ['admin_raw_event', 'event', 'happened_at']
    verbose_name_plural = 'Events'


class EmailAdmin(BaseModelAdmin):
    inlines = [EmailRecipientInline, EmailVariableInline, EmailEventInline]
    list_display = ['id', 'subject', 'sent_at', 'status', 'is_test']
    list_filter = ['status']
    search_fields = ('=from_email',)

    # Everything is readonly because this table is inherently immutable.
    # It makes no sense to edit the records of that which has already happened.
    readonly_fields = ['subject', 'html_body', 'text_body', 'from_email', 'reply_to', 'type', 'admin_text_full',
        'status', 'sent_at', 'is_test', 'communication_time', 'guid', 'admin_log', 'backend', 'text_excerpt', 'admin_html']

    def admin_html(self, obj):
        url = reverse("grapevine:view-on-site", kwargs={"message_guid": obj.guid})
        return """<iframe style="border:0; width:560px; height:500px; padding:10px 5%;" src="{}"></iframe>""".format(url)
    admin_html.short_description = 'HTML'
    admin_html.allow_tags = True

    def text_excerpt(self, obj):
        return obj.text_body[:100]
    text_excerpt.short_description = 'Text Excerpt'

    def admin_text_full(self, obj):
        return obj.text_body.replace('\n', '<br>')
    admin_text_full.short_description = 'Text Body'
    admin_text_full.allow_tags = True

    def admin_log(self, obj):
        return '<pre>%s</pre>' % (obj.log,)
    admin_log.short_description = 'Log'
    admin_log.allow_tags = True

    fieldsets = (
        ('Message Quick View', {'fields':
            ('subject', 'admin_html', 'text_excerpt', 'from_email', 'reply_to',)
        },),
        ('Full Message', {
            'classes': ('collapse',),
            'fields': ('html_body', 'admin_text_full', 'admin_log',)
        },),
        ('Status', {'fields':
            ('type', 'status', 'sent_at', 'is_test',)
        },),
        ('Stats', {'fields':
            ('communication_time', 'guid', 'backend',)
        },),
    )


class EmailRecipientAdmin(BaseModelAdmin):
    raw_id_fields = ['email']
    list_display = ['email', 'address', 'type']


class EmailBackendAdmin(BaseModelAdmin):
    list_display = ['id', 'name', 'path', 'username', 'password']
    actions = None

    def has_delete_permission(self, request, obj=None):
        return False


class RawEventAdmin(BaseModelAdmin):

    readonly_fields = ['backend', 'admin_detail_payload', 'processed_on', 'processed_in',
        'is_queued', 'is_broken', 'remote_ip', 'created_at']

    list_display = ['id', 'backend', 'admin_list_payload', 'processed_on', 'processed_in',
        'remote_ip', 'created_at']

    fieldsets = (
        ('Event',
            {'fields': ('backend', 'admin_detail_payload', 'remote_ip',)},
         ),
        ('Status',
            {'fields': ('processed_on', 'processed_in', 'is_queued', 'is_broken', 'created_at',)},
         )
    )

    def admin_list_payload(self, obj):
        payload = obj.payload.replace('\n', '')[:20]
        return payload

    def admin_detail_payload(self, obj):
        return "<pre>%s</pre>" % (obj.payload,)
    admin_detail_payload.short_description = "Payload"
    admin_detail_payload.allow_tags = True


class UnsubscribedAddressAdmin(BaseModelAdmin):
    raw_id_fields = ['email']
    list_display = ['address', 'created_at']


class EventAdmin(BaseModelAdmin):
    list_display = ['name', 'should_stop_sending']


admin.site.register(Email, EmailAdmin)
admin.site.register(EmailRecipient, EmailRecipientAdmin)
admin.site.register(EmailBackend, EmailBackendAdmin)
admin.site.register(RawEvent, RawEventAdmin)
admin.site.register(Event, EventAdmin)
admin.site.register(UnsubscribedAddress, UnsubscribedAddressAdmin)

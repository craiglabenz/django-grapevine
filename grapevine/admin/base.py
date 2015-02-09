from __future__ import unicode_literals

# Django
from django.conf.urls import url
from django.contrib import admin, messages
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse, NoReverseMatch
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404, redirect

# Local Apps
from grapevine.emails.filters import OnSpecificDateListFilter
from grapevine.utils import render_view


class BaseModelAdmin(admin.ModelAdmin):

    additional_object_tool_excludes = ()

    @property
    def model_meta_info(self):
        return (self.model._meta.app_label, self.model._meta.model_name,)

    @property
    def admin_view_info(self):
        return '%s_%s' % self.model_meta_info

    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        if obj:
            context['additional_object_tools'] = self.additional_object_tools(obj)
        return super(BaseModelAdmin, self).render_change_form(request, context, add, change, form_url, obj)

    def additional_object_tools(self, obj):
        tool_urls = []
        excludes = self.get_additional_object_tool_excludes(obj)
        for relationship in obj._meta.get_all_related_objects():
            # Skip all excludes
            if relationship.get_accessor_name() in excludes:
                continue

            remote_field_name = relationship.field.name
            try:
                url = reverse('admin:%s_%s_changelist' % (relationship.model._meta.app_label, relationship.model._meta.model_name,))
                url += '?%s=%s' % (remote_field_name, obj.pk,)

                display_name = "View %s" % (relationship.get_accessor_name().title(),)
                display_name = display_name.replace('_', ' ')
                tool_urls.append({
                    'url': url,
                    'display_name': display_name
                })
            except NoReverseMatch:
                pass

        return tool_urls

    def get_additional_object_tool_excludes(self, obj):
        """
        Returns an interable of relationship ``get_accessor_name()`` values that should **not** be automatically
        added to the additional tools section in the admin.

        Generally speaking, ``get_accessor_name()`` returns the name of the ReverseManager,
        which is what is overwritten by the ``related_name`` keyword on ForeignKey fields.
        """
        return self.additional_object_tool_excludes


class SendableInline(admin.TabularInline):

    fields = ["admin_id", "admin_message", "scheduled_send_time", "cancelled_at_send_time"]

    def admin_id(self, obj):
        url = reverse('admin:%s_change' % (obj.admin_view_info,), args=(obj.id,))
        return '<a href="%s" target="_blank">%s</a>' % (url, obj.id,)
    admin_id.allow_tags = True
    admin_id.short_description = 'Id'

    def admin_message(self, obj):
        if obj.message is None:
            return '--'

        transport_class_app_name = obj.get_transport_class()._meta.app_label
        transport_class_sluggy_name = obj.get_transport_class()._meta.verbose_name.lower().replace(' ', '_')
        url = reverse('admin:%s_%s_change' % (transport_class_app_name, transport_class_sluggy_name,), args=(obj.message_id,))
        return '<a href="%s" target="_blank" style="text-decoration:none;">%s</a>' % (url, obj.message.__unicode__(),)
    admin_message.allow_tags = True
    admin_message.short_description = 'Message'

    def has_delete_permission(self, request, obj=None):
        return True

    def has_add_permission(self, request, obj=None):
        return True

    readonly_fields = ['admin_id', 'admin_message']
    extra = 0


class SendableAdminMixin(object):
    """
    You must set `model` in any Admin classes inheriting from this
    class or nothing will work.
    """
    PREVIEW_HEIGHT = 100

    # Used for admin display purposes
    message_type_verbose = "Message"
    whitelisted_filter_fields = ()

    readonly_fields = ['admin_message']
    list_filter = (('scheduled_send_time', OnSpecificDateListFilter),)

    change_form_template = 'admin/change_sendable_form.html'

    def get_actions(self, request):
        actions = super(SendableAdminMixin, self).get_actions(request)

        # Add our custom action
        label = "Detatch from {0}".format(self.message_type_verbose)
        actions[label] = (self.__class__.detatch_messages, label, label,)

        return actions

    def detatch_messages(self, request, queryset):
        cnt = queryset.count()

        # Nothing fancy, just nuke the field.
        queryset.update(message_id=None)

        messages.add_message(request, messages.SUCCESS, "Detatched {0} {1}".format(cnt, self.message_type_verbose))
        return redirect(request.path + "?" + request.GET.urlencode())

    def lookup_allowed(self, key, value):
        """
        Normally list filtering is only *allowed* on things specified in
        ``list_filter`` above, but that's a problem because the Django admin
        wants to draw a dropdown containing all possible options. To search
        on ``model__related_model``, we would have to specify exactly that, and Django
        might try to draw a dropdown of all umpteen million records. No bien.

        Thus, we whitelist some fields ourselves as being legal edits without
        specifying them in the place where a fckng mammoth <select> field could result.
        """
        for field_name in self.whitelisted_filter_fields:
            if field_name in key:
                return True
        return super(SendableAdminMixin, self).lookup_allowed(key, value)

    def admin_message(self, obj):
        if obj.message is None:
            return '--'

        transport_class_app_name = obj.get_transport_class()._meta.app_label
        transport_class_sluggy_name = obj.get_transport_class()._meta.verbose_name.lower().replace(' ', '_')
        url = reverse('admin:%s_%s_change' % (transport_class_app_name, transport_class_sluggy_name,), args=(obj.message_id,))
        return '<a href="%s" target="_blank" style="text-decoration:none;">%s</a>' % (url, obj.message.__unicode__(),)
    admin_message.allow_tags = True
    admin_message.short_description = 'Message'

    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        context['PREVIEW_HEIGHT'] = getattr(self, "PREVIEW_HEIGHT", 300)
        if obj:
            context['preview_url'] = "data:text/html;charset=utf-8," + obj.html_body

            # Add in the message type, for nice clarity across various types of transports
            context['message_type_verbose'] = self.message_type_verbose
        return super(SendableAdminMixin, self).render_change_form(request, context, add, change, form_url, obj)

    def additional_object_tools(self, obj):
        tools = super(SendableAdminMixin, self).additional_object_tools(obj)
        tools.append({
            'url': reverse('admin:%s_send_test_message' % (self.admin_view_info,), args=(obj.pk,)),
            'display_name': 'Send Test %s' % (self.message_type_verbose,)
        })
        if not obj.is_sent or not obj.message or obj.message.status != obj.message.SENT:
            tools.append({
                'url': reverse('admin:%s_send_real_message' % (self.admin_view_info,), args=(obj.pk,)),
                'display_name': 'Send Real %s' % (self.message_type_verbose,)
            })
        return tools

    @property
    def model_meta_info(self):
        return (self.model._meta.app_label, self.model._meta.model_name,)

    @property
    def admin_view_info(self):
        return '%s_%s' % self.model_meta_info

    def get_urls(self):
        urls = super(SendableAdminMixin, self).get_urls()
        my_urls = [
            url(r'^(.+)/render/$', self.admin_site.admin_view(self.render), name='%s_render' % (self.admin_view_info,)),
            url(r'^(.+)/send-test/$', self.admin_site.admin_view(self.send_test_message), name='%s_send_test_message' % (self.admin_view_info,)),
            url(r'^(.+)/send-real/$', self.admin_site.admin_view(self.send_real_message), name='%s_send_real_message' % (self.admin_view_info,)),
        ]
        return my_urls + urls

    def send_real_message(self, request, obj_id):
        obj = get_object_or_404(self.model, pk=obj_id)
        if request.method == 'GET':

            # Load the recipients
            recipients = obj.get_normalized_recipients()

            context = {
                'obj': obj,
                'recipients': recipients,
                'opts': self.model._meta,
                'title': 'Send Real %s' % (self.message_type_verbose,)
            }
            return render_view(request, 'admin/send_real.html', context)
        elif request.method == 'POST':
            return self.send_message(request, obj, False)

    def send_test_message(self, request, obj_id):
        obj = get_object_or_404(self.model, pk=obj_id)
        if request.method == 'GET':
            context = {
                'recipients': self.get_test_recipient(request, obj_id),
                'opts': self.model._meta,
                'title': 'Send Test %s' % (self.message_type_verbose,)
            }
            return render_view(request, 'admin/send_test.html', context)
        elif request.method == 'POST':
            return self.send_message(request, obj, True, request.POST.get('recipient_address'))

    def get_test_recipient(self, request, obj_id):
        """
        No idea what makes sense against a generic Sendable
        """
        return ''

    def send_message(self, request, obj, is_test, recipient_address=None):
        if not request.user.is_authenticated() or not request.user.is_staff:
            raise Http404

        if is_test and not request.user.email:
            messages.add_message(request, messages.ERROR,
                "Current Admin user does not have a specified email address.")
            return HttpResponseRedirect(reverse("admin:%s_change" % (self.admin_view_info,), args=(obj.pk,)))

        # Load the Sendable and send a message
        is_sent = obj.send(recipient_address=recipient_address, is_test=is_test, force_resend=True)

        if is_sent:
            message_beginning = 'Test' if is_test else ''
            message_ending = 'to %s' % (recipient_address) if recipient_address else ''
            messages.add_message(request, messages.SUCCESS,
                "%s Message sent %s" % (message_beginning, message_ending,))

            content_type_id = ContentType.objects.get_for_model(obj).pk
            admin.models.LogEntry.objects.log_action(
                user_id=request.user.pk,
                content_type_id=content_type_id,
                object_id=obj.pk,
                object_repr=obj.__unicode__(),
                action_flag=admin.models.CHANGE,
                change_message='Sent %s Message Id: %s for %s Id: %s' % (message_beginning, obj.transport.pk, obj._meta.verbose_name, obj.pk,)
            )
        else:
            messages.add_message(request, messages.ERROR,
                "Problem sending email.")

        return HttpResponseRedirect(reverse('admin:%s_change' % (self.admin_view_info,), args=(obj.pk,)))

    def render(self, request, obj_id):
        if not request.user.is_authenticated() or not request.user.is_staff:
            raise Http404

        obj = get_object_or_404(self.model, pk=obj_id)
        try:
            return HttpResponse(obj.render())
        except Exception as e:
            return HttpResponse("%s: %s" % (e.__class__.__name__, e.args[0],))

# Grapevine
===========

![Downloads](https://pypip.in/download/django-grapevine/badge.png "Downloads")
--

Grapevine is a messaging system built in Django. App-specific classes that want to make use of Grapevine's internals should do so by using the pre-baked mixins and generics found in `/grapevine/mixins.py` and `/grapevine/generics.py`.

Grapevine's highest level concept is to define generic `Transport` classes (a default `Email` transport is included), and then allow various model-based `Sendable` classes to interface with them simply and cleanly.

## Emails

Grapevine's email infrastructure offers the following features:

* **Quick Previews**: `Sendable` admin change_form views render in their templates with the appropriate context, allowing you to know exactly how emails will look, to click on and verify any links, etc.
* **Easy Test Sending**: Send real or test emails from any `Sendable` change_form view. Getting your templates into Litmus has never been easier.
* **In-admin Email Tracking**: All `Sendable` models can easily be used as admin inline models on their "host" model (likely your core User model). This allows everyone to easy see who's been emailed what, and when.
* **Email introspection**: All details about your emails are saved, including their fully formed HTML and plain text  versions, recipients (TO, CC, and BCC), and any variables/categories sent to your third party email sender.
* **Multiple 3rd Party Senders**: Use through any 3rd party sender you like. Even use multiple simultaneously, routing priority emails through special IPs and marketing emails through a bulk IP.
* **Performance Tracking**: Easily accept 3rd party event webhooks to know exactly which if your emails were opened, clicked, etc. SendGrid is currently supported and Mailgun is in progress.

### Installation

Per usual, run `pip install django-grapevine` to install Grapevine into your virtual environment.

Add Grapevine to your `INSTALLED_APPS`:

```py
INSTALLED_APPS = (
	...
    'grapevine',
    'grapevine.emails',
    ...
)
```
---

### Usage
Grapevine introduces the idea of a *Sendable*. The concept is that you mark a certain model as being "Sendable", and it then exists for the sole purpose of logging communications of that specific variety. For example, you might have a `WelcomeEmail` model that is sent to each user after successful registration. Such a class definition would probably look something like this:

In `querysets.py`

```py
from grapevine.querysets import SendableQuerySet

class WelcomeEmailQuerySet(SendableQuerySet):
    # add any additional functions here
```


In `models.py`
```py
from grapevine import generics
from .querysets import WelcomeEmailQuerySet

try:
    # Not needed in Django 1.7+
    from model_utils.managers import PassThroughManager
except ImportError:
    pass

class WelcomeEmail(generics.EmailSendable):
    user = models.ForeignKey('AUTH_USER_MODEL')
    ...

    try:
        # In Django 1.7, this is finally addressed!
        objects = WelcomeEmailQuerySet.as_manager()
    except AttributeError:
        objects = PassThroughManager.for_queryset_class(WelcomeEmailQuerySet)

    def get_template_name(self):
        return 'path/to/template.html'

    def compile_context(self):
        return {
              "sendable": self,
              "user": self.user,
              "user_full_name": self.user.full_name,
         }

    def get_recipients(self):
        return "%s <%s>" % (self.user.full_name, self.user.email,)

    def get_raw_subject(self):
        return "Welcome to Acme Website, {{user_full_name}}!"

    def final_send_check(self):
        """
        Optional last-second check to make sure we still want to send
        this message. Useful if we scheduled this message far in the future,
        or threw it on a queue and suspect things may have changed.

        Should return True to still send, False to not send.
        """
        if self.user.is_active:
            return True
        else:
            # If the user has already deactivated themselves,
            # forever remove this message from the system.
            self.cancelled_at_send_time = True
            self.save()
            return False
```

In `admin.py`
```py
# Django
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

# 3rd Party
from grapevine.admin_base import BaseModelAdmin, SendableInline
from grapevine.emails.admin import EmailableAdminMixin

# Local Apps
from my_apps import models
# etc etc


class WelcomeEmailInline(SendableInline):
    model = WelcomeEmail


class UserAdmin(DjangoUserAdmin):
    inlines = [WelcomeEmailInline]


class WelcomeEmailAdmin(EmailableAdminMixin, BaseModelAdmin):
    raw_id_fields = ["user"]
    list_display = ["id", "user", "admin_message"]

    preview_height = 200

    fieldsets = (
        ('Main', {"fields": ("user",)},),
        ('Message', {"fields": ("admin_message", "scheduled_send_time",)},),
    )


admin.site.unregister(get_user_model())
admin.site.register(get_user_model(), UserAdmin)
admin.site.register(WelcomeEmail, WelcomeEmailAdmin)
```


The above model/admin definitions will buy you a nice admin interface with:

A) An inline for the email on your User model:

![Sendable Inline](https://raw.githubusercontent.com/craiglabenz/django-grapevine/master/media/sendable-inline.png "Sendable Inline")

B) And an detail view for the email itself with live template rendering. This can be a huge help for non-technical support staff using the admin to schedule future emails:

![Sendable Admin](https://raw.githubusercontent.com/craiglabenz/django-grapevine/master/media/sendable-admin.png "Sendable Admin")

---
### Tracking Email Performance

Grapevine provides infrastructure for opening up webhooks to listen to your 3rd party's event notifications. Add the following line to your root URLs conf to begin:

```py
urlpatterns = [
    ...
    url(r'^grapevine/', include('grapevine.urls', namespace='grapevine')),
    ...
]
```

This opens up one URL per backend that will accept and `POST`ed payloads from SendGrid, Mailgun, etc. The URLs are of the form:

```py
^grapevine/backends/sendgrid/events/$
^grapevine/backends/mailgun/events/$
etc
```

The view at which these URLs point only writes the raw `POST`ed payload. No processing is done because if your applications sends serious email volumes, real-time processing of event information payloads can crush your entire production database. Currently, the included SendGrid backend provides the necessary logic to process its payloads in the function `process_event()` as per SendGrid's current documentation.

#### Viewing Email Performance:

Once email event payloads are being accepted and processed, the following read-only inline on the `Email` model will offer insights:

![Processed Events](https://raw.githubusercontent.com/craiglabenz/django-grapevine/master/media/processed-events.png "Processed Events")


---

### Defining a new Transport

The first step to defining a new transport subclass is to, obviously, inherit from `Transport`. The following interface, used on a HipChat example, is available:

```py
class HipChat(Transport):

    field_specific_to_hipchat = models.CharField(max_length=255)

    class Meta(Transport.Meta):
        verbose_name = "Hipchat Message"
        verbose_name_plural = "Hipchat Messages"

    def pre_save(self):
        """
        Optional. A no-op by default.
        """
        pass

    def post_save(self):
        """
        Optional. A no-op by default.
        """
        pass

    def _send(self):
        """
        Required. This is the actual bits-on-the-wire method.
        A `NotImplementedError` will be raised if this method
        is not defined.
        """
        resp = requests.post('https://api.hipchat.com/my/specific/uri/', {"message": "payload"})
        if resp.status_code == 200:
            return True
        else:
            etc etc

     @classmethod
     def finish_initial_data(cls, sendable, data, **kwargs):
        """
        Optional, but if implemented, *must* return ``data``.
        """
        data['field_specific_to_hipchat'] = sendable.get_something_i_need()
        return data
```


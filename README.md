# Grapevine


Grapevine is a messaging system built in Django. App-specific classes that want to make use of Grapevine's internals should do so by using the pre-baked mixins and generics found in `/grapevine/mixins.py` and `/grapevine/generics.py`.

This system introduces the idea of a *Sendable*. The concept is that you mark a certain model as being "Sendable", and it then exists for the sole purpose of logging communications of that specific variety. For example, you might have a `WelcomeEmail` model that is sent to each user after successful registration. Such a class definition would probably look something like this:

```py
# querysets.py
from grapevine.querysets import SendableQuerySet

class WelcomeEmailQuerySet(SendableQuerySet):
    # add any additional functions here


# models.py
from grapevine import generics
from querysets import WelcomeEmailQuerySet

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


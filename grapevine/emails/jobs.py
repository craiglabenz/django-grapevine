from __future__ import unicode_literals
import inspect

# 3rd Party
# from celery import shared_task

# Local Apps
from . import backends


# @shared_task
def async_process_events(limit=300):
    for attr_name in dir(backends):
        attr = getattr(backends, attr_name)
        if inspect.isclass(attr) and issubclass(attr, backends.base.GrapevineEmailBackend) and hasattr(attr, 'process_events'):
            backend = attr()
            backend.process_events(limit)

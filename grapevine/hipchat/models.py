from __future__ import unicode_literals

import requests

# Django
from django.db import models
from django.conf import settings
from django.utils import timezone, six, module_loading
from django.utils.html import strip_tags

# 3rd Party
import html2text

# Local Apps
from grapevine.models import BaseModel
from grapevine.settings import grapevine_settings
from grapevine.models import Transport
from core import utils
from core.utils import logging_class

@logging_class
class HipChat(Transport):
    GENERAL_TALKS = 130723
    DATABASE_DISCUSSIONS = 130743
    GITHUB = 150746
    SOLUTIONS_TEAM = 202172
    JENKINS = 208896
    QA = 230576
    GROWTH_HACKING = 345591
    EMAILS = 362339
    BACKEND_TEAM = 391362
    NN_DESIGNS = 464123
    REVIEW_TASKFORCE = 470669
    SERVER_ALERTS = 473245
    ADS_TEAM = 473779
    FRONT_END_DISCUSSIONS = 474520
    CAMPAIGN_TEAM = 494179
    IVORY = 497734
    CBWM = 498360
    CASE_STUDY = 546354
    SALESFORCE = 563824
    SUPPORT = 581333
    ROOM_CHOICES = (
        (GENERAL_TALKS, 'General Talks'),
        (DATABASE_DISCUSSIONS, 'Database Discussions'),
        (GITHUB, 'Github'),
        (SOLUTIONS_TEAM, 'Solutions Team'),
        (JENKINS, 'Jenkins'),
        (QA, 'QA'),
        (GROWTH_HACKING, 'Growth Hacking'),
        (EMAILS, 'Emails'),
        (BACKEND_TEAM, 'Backend Team'),
        (NN_DESIGNS, '99 designs'),
        (REVIEW_TASKFORCE, 'Review Taskforce'),
        (SERVER_ALERTS, 'Server Alerts'),
        (ADS_TEAM, 'Ads team'),
        (FRONT_END_DISCUSSIONS, 'Front End Discussions'),
        (CAMPAIGN_TEAM, 'Campaign Team'),
        (IVORY, 'Ivory'),
        (CBWM, 'CBWM'),
        (CASE_STUDY, 'Case Study'),
        (SALESFORCE, 'Salesforce'),
        (SUPPORT, 'Support'),
    )
    to = models.IntegerField(choices=ROOM_CHOICES, default=IVORY, help_text="The HipChat Room Id")


    YELLOW = 'yellow'
    RED = 'red'
    GREEN = 'green'
    PURPLE = 'purple'
    GRAY = 'gray'
    COLOR_CHOICES = (
        (YELLOW, 'Yellow'),
        (RED, 'Red'),
        (GREEN, 'Green'),
        (PURPLE, 'Purple'),
        (GRAY, 'Gray'),
    )
    color = models.CharField(max_length=50, choices=COLOR_CHOICES, default=YELLOW)

    FORMAT_HTML = 'html'
    FORMAT_TEXT = 'gray'
    FORMAT_CHOICES = (
        (FORMAT_HTML, 'HTML'),
        (FORMAT_TEXT, 'Text'),
    )
    message_format = models.CharField(max_length=50, choices=FORMAT_CHOICES, default=FORMAT_HTML)


    NO = 0
    YES = 1
    NOTIFY_CHOICES = (
        (YES, 'Yes'),
        (NO, 'No'),
    )
    should_notify = models.IntegerField(choices=NOTIFY_CHOICES, default=NO)

    from_name = models.CharField(max_length=255)

    class Meta:
        verbose_name = 'HipChat'
        verbose_name_plural = 'HipChats'

    @staticmethod
    def finish_initial_data(sendable, initial_data, **kwargs):
        initial_data['to'] = sendable.TO
        initial_data['color'] = sendable.MESSAGE_COLOR
        initial_data['should_notify'] = sendable.SHOULD_NOTIFY
        initial_data['from_name'] = sendable.FROM_NAME
        return initial_data

    @property
    def message(self):
        if self.message_format and self.message_format == self.FORMAT_HTML:
            return self.html_body
        else:
            return self.text_body

    @message.setter
    def message(self, value):
        """
        Set both values logically
        """
        self.html_body = value
        self.text_body = strip_tags(value)

    @property
    def hipchat_url(self):
        return "https://api.hipchat.com/v1/rooms/message?auth_token=%s" % settings.HIPCHAT_TOKEN

    def _send(self):
        """
        Required. Send the hipchat notification
        """
        logger = utils.create_logger(HipChat, '_send')

        try:
            if self.message and self.from_name:
                self.resp = requests.post(
                    self.hipchat_url,
                    params={
                        "room_id": self.to,
                        "from": self.from_name,
                        "message": self.message,
                        "color": self.color,
                        "format": self.message_format,
                        "notify": self.should_notify
                    })

                if self.resp.status_code == 200:
                    return True
                else:
                    logger.error('HipChat Error: %s' % e)
        except Exception as e:
            logger.error(e)

        return False

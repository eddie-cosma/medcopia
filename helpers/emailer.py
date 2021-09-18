import os
import smtplib
import ssl
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import make_msgid, formatdate
from functools import wraps
from time import sleep
from urllib.parse import urlunparse

import jinja2
from validate_email import validate_email

from config import config
from models import User


def validate(address: str) -> bool:
    return validate_email(
        address,
        check_format=True,
        check_blacklist=True,
        check_dns=True,
        check_smtp=False,
    )


def render_template(template_name, **context):
    template_folder_uri = config['ROOT'] / f'signup/templates/'
    return jinja2.Environment(
        loader=jinja2.FileSystemLoader(template_folder_uri)
    ).get_template(template_name).render(context)


def exclude_during_testing(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if os.getenv('TESTING', 'False') == 'False':
            func(*args, **kwargs)

    return wrapper


class Message:
    def __init__(self,
                 recipient: User,
                 subject: str,
                 html: str = None,
                 sender: str = None,
                 reply_to: str = None,
                 extra_headers: dict[str, str] = None,
                 ):

        self.recipient = recipient
        self.subject = subject

        self.sender = sender or config['MAIL_DEFAULT_SENDER']
        self.reply_to = reply_to or config['MAIL_DEFAULT_SENDER']
        self.extra_headers = extra_headers

        self.msgId = make_msgid()
        self.date = formatdate()

        self.mime_message = self.make_message()

        if html:
            self.html = html

    def make_message(self):
        message = MIMEMultipart('alternative')
        message['From'] = self.sender
        message['To'] = self.recipient.email
        message['Subject'] = self.subject
        message['Reply-To'] = self.reply_to
        message['Message-ID'] = self.msgId
        message['Date'] = self.date
        if self.recipient.opt_out_code:
            message['List-Unsubscribe'] = f'<{self.get_unsubscribe_url()}>'
        if self.extra_headers:
            for header, value in self.extra_headers.items():
                message[header] = value
        return message

    @property
    def html(self):
        return self._html

    @html.setter
    def html(self, html):
        self._html = html
        self.mime_message.attach(MIMEText(html, 'html'))

    @exclude_during_testing
    def send(self):
        host = config['MAIL_SERVER']
        port = config['MAIL_PORT']
        username = config['MAIL_USERNAME']
        password = config['MAIL_PASSWORD']
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(host, port, context=context) as server:
            server.login(username, password)
            server.sendmail(self.sender, self.recipient.email, self.mime_message.as_string())

    def get_unsubscribe_url(self):
        scheme = config['PREFERRED_URL_SCHEME']
        netloc = config['SERVER_NAME']
        path = '/unsubscribe/' + self.recipient.opt_out_code
        return urlunparse((scheme, netloc, path, '', '', ''))

    def render_template(self, template: str, recipient: User, **template_args) -> str:
        unsubscribe_url = self.get_unsubscribe_url()
        return render_template(
            template,
            recipient=recipient,
            unsubscribe_url=unsubscribe_url,
            **template_args,
        )


class MassMessage:
    def __init__(self,
                 recipients: list[User],
                 subject: str,
                 template_name: str,
                 sender: str = None,
                 reply_to: str = None,
                 extra_headers: dict[str, str] = None,
                 max_per_hour: int = 200,
                 **template_args,
                 ):
        self.messages = []
        for recipient in recipients:
            message = Message(
                recipient=recipient,
                subject=subject,
                sender=sender,
                reply_to=reply_to,
                extra_headers=extra_headers,
            )
            message.html = message.render_template(template_name, recipient, **template_args)
            self.messages.append(message)

        self.delay = 1 / (max_per_hour / 60 / 60)

    @exclude_during_testing
    def send_all(self):
        host = config['MAIL_SERVER']
        port = config['MAIL_PORT']
        username = config['MAIL_USERNAME']
        password = config['MAIL_PASSWORD']
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(host, port, context=context) as server:
            server.login(username, password)
            for message in self.messages:
                server.sendmail(message.sender, message.recipient.email, message.mime_message.as_string())
                message.recipient.last_message_time = datetime.utcnow()
                sleep(self.delay)

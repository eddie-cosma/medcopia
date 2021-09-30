import os
import re
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

from config import config
from models import User, Session


def validate(address: str) -> bool:
    return True if re.fullmatch(r'[\w\.-]+@[\w\.-]+(\.[\w]+)+', address) else False


def render_template(template_name, **context):
    """Render a :py:mod:`jinja2` template without a :py:mod:`flask` context."""
    template_folder_uri = config['ROOT'] / f'signup/templates/'
    return jinja2.Environment(
        loader=jinja2.FileSystemLoader(template_folder_uri)
    ).get_template(template_name).render(context)


def exclude_during_testing(func):
    """Exclude wrapped function when ``TESTING`` environmental variable is ``True``."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if os.getenv('TESTING', 'False') == 'False':
            func(*args, **kwargs)

    return wrapper


class Message:
    """Represents an email message."""

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

        self._logo_path = '/static/logo.png'
        self._unsubscribe_path = '/unsubscribe/' + self.recipient.opt_out_code

        self.mime_message = self.make_message()

        if html:
            self.html = html

    def make_message(self):
        """Create a :py:class:`email.mime.multipart.MIMEMultipart` message with instance parameters."""
        message = MIMEMultipart('alternative')
        message['From'] = self.sender
        message['To'] = self.recipient.email
        message['Subject'] = self.subject
        message['Reply-To'] = self.reply_to
        message['Message-ID'] = self.msgId
        message['Date'] = self.date
        if self.recipient.opt_out_code:
            message['List-Unsubscribe'] = f'<{self.get_external_url(self._unsubscribe_path)}>'
        if self.extra_headers:
            for header, value in self.extra_headers.items():
                message[header] = value
        return message

    @property
    def html(self):
        """Get the html body of the email."""
        return self._html

    @html.setter
    def html(self, html):
        """Attach a new html body to the email, replacing the old one."""
        self._html = html
        self.mime_message.attach(MIMEText(html, 'html'))

    @exclude_during_testing
    def send(self):
        """Send the email using the preconfigured SMTP settings.

        .. note::
            Currently only implicit SSL/TLS authentication is supported.
            STARTTLS and unencrypted sending are not available.
        """
        host = config['MAIL_SERVER']
        port = config['MAIL_PORT']
        username = config['MAIL_USERNAME']
        password = config['MAIL_PASSWORD']
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(host, port, context=context) as server:
            server.login(username, password)
            server.sendmail(self.sender, self.recipient.email, self.mime_message.as_string())

    @staticmethod
    def get_external_url(path: str) -> str:
        """Add a url scheme and server to a specified url path.

        :param path: the full url path to the file on the server, as
            accessible by the end user in the browser.
        :return: the same path with a url scheme and server name appended
            to the front.
        """
        scheme = config['PREFERRED_URL_SCHEME']
        netloc = config['SERVER_NAME']
        return urlunparse((scheme, netloc, path, '', '', ''))

    def render_template(self, template: str, recipient: User, **template_args) -> str:
        """Render html template for a specified :py:class:`models.database.User`.

        :param template: the name of the template file in the
                         signup/templates/ folder.
        :param recipient: User who will receive the email.
        :param template_args: additional context arguments to pass to
                              jinja2.
        :return: rendered html template.
        """
        unsubscribe_url = self.get_external_url(self._unsubscribe_path)
        return render_template(
            template,
            recipient=recipient,
            logo_uri=self.get_external_url(self._logo_path),
            unsubscribe_url=unsubscribe_url,
            **template_args,
        )


class MassMessage:
    """Represents a mass mailing with many recipients.

    User-specific emails are generated using the specified parameters. This
    is important so each recipient gets a custom unsubscribe link.
    """

    def __init__(self,
                 db_session: Session,
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

        self._session = db_session

    @exclude_during_testing
    def send_all(self):
        """Send queued user-specific emails sequentially.

        A delay based on the :attr:`max_per_hour` instance attribute is used
        to prevent abuse of the SMTP server. Send times are logged in the
        database in case of failure.
        """
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
                self._session.commit()
                sleep(self.delay)

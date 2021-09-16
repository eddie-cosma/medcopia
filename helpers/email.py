import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import make_msgid, formatdate
from time import sleep

from flask import render_template

from models import CONFIG
from signup import create_app
from validate_email import validate_email


def validate(address: str) -> bool:
    return validate_email(
        address,
        check_format=True,
        check_blacklist=True,
        check_dns=True,
        check_smtp=False,
    )


class Recipient:
    def __init__(self,
                 address: str,
                 unsubscribe_token: str = None):
        self.address = address
        self.unsubscribe_token = unsubscribe_token


class Message:
    def __init__(self,
                 recipient: Recipient,
                 subject: str,
                 html: str,
                 sender: str = None,
                 reply_to: str = None,
                 extra_headers: dict[str, str] = None,
                 ):
        self.recipient = recipient
        self.subject = subject
        self.html = html

        self.sender = sender or CONFIG['MAIL_DEFAULT_SENDER']
        self.reply_to = reply_to or CONFIG['MAIL_DEFAULT_SENDER']
        self.extra_headers = extra_headers

        self.msgId = make_msgid()
        self.date = formatdate()

        self._html = MIMEText(self.html, 'html')
        self.mime_message = self.make_message()

    def make_message(self):
        message = MIMEMultipart('alternative')
        message['From'] = self.sender
        message['To'] = self.recipient.address
        message['Subject'] = self.subject
        message['Reply-To'] = self.reply_to
        message['Message-ID'] = self.msgId
        message['Date'] = self.date
        if self.extra_headers:
            for header, value in self.extra_headers.items():
                message[header] = value
        message.attach(self._html)
        return message

    def send(self):
        host = CONFIG['MAIL_SERVER']
        port = CONFIG['MAIL_PORT']
        username = CONFIG['MAIL_USERNAME']
        password = CONFIG['MAIL_PASSWORD']
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(host, port, context=context) as server:
            server.login(username, password)
            server.sendmail(self.sender, self.recipient.address, self.mime_message.as_string())

    @staticmethod
    def render_template(template: str, recipient: Recipient) -> str:
        signup_app = create_app()
        with signup_app.app_context():
            return render_template(template, recipient=recipient)


class MassMessage:
    def __init__(self,
                 recipients: list[Recipient],
                 subject: str,
                 template_name: str,
                 sender: str = None,
                 reply_to: str = None,
                 extra_headers: dict[str, str] = None,
                 max_per_hour: int = 200,
                 ):
        self.messages = []
        for recipient in recipients:
            html = Message.render_template(template_name, recipient)
            message = Message(
                recipient=recipient,
                subject=subject,
                html=html,
                sender=sender,
                reply_to=reply_to,
                extra_headers=extra_headers,
            )
            self.messages.append(message)

        self.delay = 1 / (max_per_hour / 60 / 60)

    def send_all(self):
        host = CONFIG['MAIL_SERVER']
        port = CONFIG['MAIL_PORT']
        username = CONFIG['MAIL_USERNAME']
        password = CONFIG['MAIL_PASSWORD']
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(host, port, context=context) as server:
            server.login(username, password)
            for message in self.messages:
                server.sendmail(message.sender, message.recipient.address, message.mime_message.as_string())
                sleep(self.delay)

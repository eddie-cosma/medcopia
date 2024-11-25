import re
import time
from datetime import datetime
from typing import Any

from sendgrid import SendGridAPIClient

from config import config
from models import User, Session


def validate(address: str) -> bool:
    return True if re.fullmatch(r'[\w\.-]+@[\w\.-]+(\.[\w]+)+', address) else False


class Message:
    """Represents a SendGrid email message."""

    def __init__(self,
                 recipients: list[User],
                 subject: str,
                 template_id: str,
                 template_data: dict[str, Any],
                 sender: str = config.get('MAIL_DEFAULT_SENDER'),
                 asm_group: int = int(config.get('MAIL_DEFAULT_ASM_GROUP')),
                 timestamp: str = time.time(),
                 session=Session(),
                 ):

        self.recipients = recipients
        self.subject = subject
        self.template_id = template_id
        self.template_data = template_data
        self.template_data['timeStamp'] = timestamp
        self.sender = sender
        self.asm_group = asm_group

        self._generate_request_body()

        self.status_code = None
        self.body = None
        self.headers = None

        self.session = session

    def _generate_request_body(self):
        """Generate the request body to attach to SendGrid request."""
        self.request_body = {
            'personalizations': [],
            'from': {'email': self.sender},
            'asm': {'group_id': self.asm_group},
            'template_id': self.template_id,
        }

        for recipient in self.recipients:
            self.request_body['personalizations'].append({
                'to': [{'email': recipient.email}],
                'subject': self.subject,
                'dynamic_template_data': self.template_data,
            })

    def _update_email_send_time(self):
        """Update the last-sent time for each user in the database."""
        for recipient in self.recipients:
            recipient.last_message_time = datetime.now()
            self.session.add(recipient)
        self.session.commit()

    def send(self):
        """Send the message using SendGrid API and log the result."""
        sg = SendGridAPIClient(api_key=config.get('SENDGRID_API_KEY'))
        # TODO: Add a try catch here for python_http_client.exceptions.BadRequestsError 400 and others
        response = sg.client.mail.send.post(request_body=self.request_body)
        self.status_code = response.status_code
        self.body = response.body
        self.headers = response.headers

        if self.success:
            self._update_email_send_time()

    @property
    def success(self):
        """Return True if message was sent successfully."""
        if self.status_code == 202:
            return True
        else:
            return False

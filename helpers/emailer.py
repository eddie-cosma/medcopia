import re
import time
from typing import Any

from python_http_client import HTTPError
from sendgrid import SendGridAPIClient

from config import config
from models import User, Session, EmailLog, EmailType


def validate(address: str) -> bool:
    return True if re.fullmatch(r'[\w\.-]+@[\w\.-]+(\.[\w]+)+', address) else False


class Message:
    """Represents a SendGrid email message."""

    def __init__(self,
                 recipients: list[User],
                 type: EmailType,
                 template_id: str,
                 template_data: dict[str, Any],
                 sender: str = config.get('MAIL_DEFAULT_SENDER'),
                 asm_group: int = int(config.get('MAIL_DEFAULT_ASM_GROUP')),
                 timestamp: str = time.time(),
                 session=Session(),
                 ):

        self.recipients = recipients
        self.type = type
        self.template_id = template_id
        self.template_data = template_data
        self.template_data['timeStamp'] = timestamp
        self.sender = sender
        self.asm_group = asm_group

        self._set_subject()
        self._generate_request_body()

        self.status_code = None
        self.body = None
        self.headers = None

        self.session = session

    @property
    def success(self):
        """Return True if message was sent successfully."""
        if self.status_code == 202:
            return True
        else:
            return False

    def _set_subject(self):
        if self.type == EmailType.OPT_IN:
            self.subject = 'Confirm drug shortage alert subscription'
        elif self.type == EmailType.SHORTAGE_ALERT:
            self.subject = 'Medcopia shortage alert'
        else:
            self.subject = ''

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

    def _log(self):
        """Create a log item for each message sent."""
        logged_messages = []
        for recipient in self.recipients:
            log_message = EmailLog(
                user=recipient,
                type_id=self.type.value,
                status_code=self.status_code,
            )
            logged_messages.append(log_message)
        self.session.add_all(logged_messages)
        self.session.commit()

    def send(self):
        """Send the message using SendGrid API and log the result."""

        # If we are running tests, simulate a successful email without sending
        if config.get('TESTING'):
            self.status_code = 202
            self._log()
            return

        sg = SendGridAPIClient(api_key=config.get('SENDGRID_API_KEY'))
        try:
            response = sg.client.mail.send.post(request_body=self.request_body)
        except HTTPError as e:
            response = e

        self.status_code = response.status_code
        self.body = response.body
        self.headers = response.headers

        self._log()

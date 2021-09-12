from flask import current_app, render_template, url_for
from flask_mail import Message
from validate_email import validate_email

from . import mail


def validate(address: str) -> bool:
    return validate_email(
        address,
        check_format=True,
        check_blacklist=True,
        check_dns=True,
        check_smtp=False,
    )


def send_confirmation(address: str, confirm_token: str, unsubscribe_token: str):
    unsubscribe_link = url_for(
        "shortage.unsubscribe",
        token=unsubscribe_token,
        _external=True,
    )
    email = Message(
        subject="Confirm drug shortage alert subscription",
        sender=current_app.config["MAIL_DEFAULT_SENDER"],
        recipients=[address],
        reply_to=current_app.config["MAIL_DEFAULT_SENDER"],
        html=render_template('email.html', email=address, token=confirm_token),
        extra_headers={
            'List-Unsubscribe': f'<{unsubscribe_link}>',
        }
    )
    mail.send(email)

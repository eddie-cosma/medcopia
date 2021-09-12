from flask import current_app, render_template, url_for
from flask_mail import Message

from . import mail


def send_confirmation(address: str, confirm_token: str, unsubscribe_token: str):
    email = Message(
        subject="Confirm drug shortage alert subscription",
        sender=current_app.config["MAIL_DEFAULT_SENDER"],
        recipients=[address],
        reply_to='noreply@cosmanaut.com',
        html=render_template('email.html', email=address, token=confirm_token),
        extra_headers={
            'List-Unsubscribe': url_for('shortage.unsubscribe', email=address, token=unsubscribe_token, _external=True)
        }
    )
    mail.send(email)

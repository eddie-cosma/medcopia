"""Miscellaneous utilities to support the web application. This needs to be
restructured in future versions."""

from __future__ import annotations

import os

from flask import current_app, url_for
from itsdangerous import URLSafeSerializer

from helpers.emailer import Message
from models import User
from signup import db

opt_in_serializer = URLSafeSerializer(current_app.config['SECRET_KEY'], salt='opt_in')


def generate_keys(email: str):
    """Generate opt-in codes for a newly registered user."""
    if registrant := db.session.query(User).filter_by(email=email).one_or_none():
        registrant.opt_in_code = opt_in_serializer.dumps(registrant.email)
        registrant.opt_ins_sent = 0
        db.session.commit()


def send_opt_in_confirmation(email: str):
    """Send newly registered user a confirmation email."""
    if registrant := db.session.query(User).filter_by(email=email).one_or_none():
        confirm_uri = url_for('shortage.confirm', token=registrant.opt_in_code, _external=True)
        email = Message(
            recipients=[registrant],
            subject="Confirm drug shortage alert subscription",
            template_id=current_app.config['MAIL_CONFIRM_TEMPLATE'],
            template_data={"confirm_uri": confirm_uri},
            session=db.session,
        )
        if os.getenv('TESTING', 'False') == 'False':
            email.send()
        registrant.opt_ins_sent += 1
        db.session.add(registrant)
        db.session.commit()


def verify_token(token: str) -> bool | str:
    """Verify that an opt-in code is valid.

    :param token: the opt-in code
    :return: email address if the code is valid, ``False`` otherwise.
    """
    try:
        email = opt_in_serializer.loads(token)
    except:
        return False

    if not (registrant := db.session.query(User).filter_by(email=email).one_or_none()):
        return False

    if registrant.opt_in_code:
        registrant.opt_in_code = None
        db.session.add(registrant)
        db.session.commit()
        return email

    return False

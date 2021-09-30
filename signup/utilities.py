"""Miscellaneous utilities to support the web application. This needs to be
restructured in future versions."""

from __future__ import annotations

import os

from flask import current_app, render_template
from itsdangerous import URLSafeSerializer

from helpers.emailer import Message
from models import User
from signup import db

opt_in_serializer = URLSafeSerializer(current_app.config['SECRET_KEY'], salt='opt_in')
opt_out_serializer = URLSafeSerializer(current_app.config['SECRET_KEY'], salt='opt_out')


def generate_keys(email: str):
    """Generate opt-in and opt-out codes for a newly registered user."""
    if registrant := db.session.query(User).filter_by(email=email).one_or_none():
        registrant.opt_in_code = opt_in_serializer.dumps(registrant.email)
        registrant.opt_out_code = opt_out_serializer.dumps(registrant.email)
        registrant.opt_ins_sent = 0
        db.session.commit()


def send_opt_in_confirmation(email: str):
    """Send newly registered user a confirmation email."""
    if registrant := db.session.query(User).filter_by(email=email).one_or_none():
        email = Message(
            subject="Confirm drug shortage alert subscription",
            sender=current_app.config["MAIL_DEFAULT_SENDER"],
            recipient=registrant,
            reply_to=current_app.config["MAIL_DEFAULT_SENDER"],
            html=render_template('email.html', recipient=registrant),
        )
        if os.getenv('TESTING', 'False') == 'False':
            email.send()
        registrant.opt_ins_sent += 1
        db.session.add(registrant)
        db.session.commit()


def verify_token(token: str, token_type: str = 'opt_in') -> bool | str:
    """Verify that an opt-in or opt-out code is valid.

    :param token: the opt-in or opt-out code
    :param token_type: string literal ``'opt_in'`` or ``'opt_out'`` depending
                       on the type of code passed.
    :return: ``True`` if the code is valid, ``False`` otherwise.
    """
    if token_type == 'opt_in':
        serializer = opt_in_serializer
    elif token_type == 'opt_out':
        serializer = opt_out_serializer
    else:
        raise ValueError('Invalid serializer type. Must be either "opt_in" or "opt_out".')

    try:
        email = serializer.loads(token)
    except:
        return False

    if not (registrant := db.session.query(User).filter_by(email=email).one_or_none()):
        return False

    if token_type == 'opt_in' and registrant.opt_in_code:
        registrant.opt_in_code = None
        db.session.add(registrant)
        db.session.commit()
        return email
    elif token_type == 'opt_out':
        db.session.delete(registrant)
        db.session.commit()
        return True

    return False

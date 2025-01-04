"""Miscellaneous utilities to support the web application. This needs to be
restructured in future versions."""

from __future__ import annotations

from datetime import datetime, timedelta

from flask import current_app, url_for, flash
from itsdangerous import URLSafeSerializer
from sqlalchemy import func, and_

from helpers.emailer import Message
from models import User, EmailType, EmailLog
from signup import db

opt_in_serializer = URLSafeSerializer(current_app.config['SECRET_KEY'], salt='opt_in')


def generate_keys(email: str):
    """Generate opt-in codes for a newly registered user."""
    if registrant := db.session.query(User).filter_by(email=email).one_or_none():
        registrant.opt_in_code = opt_in_serializer.dumps(registrant.email)
        registrant.opt_ins_sent = 0
        db.session.commit()


def count_todays_opt_ins_sent(user: User) -> int:
    """Get the number of opt-in emails the user requested today"""

    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    opt_ins_sent = db.session.query(func.count(EmailLog.id)).filter(
        and_(
            EmailLog.sent_time >= today_start,
            EmailLog.sent_time < today_end,
            EmailLog.user_id == user.id,
        )
    ).scalar()
    return opt_ins_sent

def send_opt_in_confirmation(email: str):
    """Send newly registered user a confirmation email."""

    if registrant := db.session.query(User).filter_by(email=email).one_or_none():
        opt_ins_sent = count_todays_opt_ins_sent(registrant)
        if opt_ins_sent < 5:
            confirm_uri = url_for('shortage.confirm', token=registrant.opt_in_code, _external=True)
            email = Message(
                recipients=[registrant],
                type=EmailType.OPT_IN,
                template_id=current_app.config['MAIL_CONFIRM_TEMPLATE'],
                template_data={"confirm_uri": confirm_uri},
                session=db.session,
            )
            email.send()
            db.session.add(registrant)
            db.session.commit()
        else:
            service_address = current_app.config['MAIL_DEFAULT_SENDER']
            flash(f'Only five confirmation emails may be sent per day to prevent our emails being \
            marked as spam. Please wait until tomorrow or contact {service_address} for assistance.')


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

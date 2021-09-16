from __future__ import annotations

from flask import current_app
from itsdangerous import URLSafeSerializer

from models import User
from signup import db
from signup.email import send_confirmation


opt_in_serializer = URLSafeSerializer(current_app.config['SECRET_KEY'], salt='opt_in')
opt_out_serializer = URLSafeSerializer(current_app.config['SECRET_KEY'], salt='opt_out')


def generate_keys(email: str):
    if registrant := db.session.query(User).filter_by(email=email).one_or_none():
        registrant.opt_in_code = opt_in_serializer.dumps(registrant.email)
        registrant.opt_out_code = opt_out_serializer.dumps(registrant.email)
        registrant.opt_ins_sent = 0
        db.session.commit()


def send_opt_in_confirmation(email: str):
    if registrant := db.session.query(User).filter_by(email=email).one_or_none():
        send_confirmation(email, registrant.opt_in_code, registrant.opt_out_code)
        registrant.opt_ins_sent += 1
        db.session.commit()


def verify_token(token: str, token_type: str = 'opt_in') -> bool | str:
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
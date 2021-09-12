from __future__ import annotations

from flask import current_app
from itsdangerous import URLSafeSerializer

from . import db

opt_in_serializer = URLSafeSerializer(current_app.config['SECRET_KEY'], salt='opt_in')
opt_out_serializer = URLSafeSerializer(current_app.config['SECRET_KEY'], salt='opt_out')


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), nullable=False, unique=True)
    opt_in_code = db.Column(db.String(255), nullable=True)
    opt_out_code = db.Column(db.String(255), nullable=True)
    created_date = db.Column(db.DateTime(timezone=False), nullable=False, server_default=db.func.now())
    modified_date = db.Column(db.DateTime(timezone=False), nullable=True, onupdate=db.func.now())

    @classmethod
    def generate_keys(cls, email: str):
        if registrant := db.session.query(cls).filter_by(email=email).one_or_none():
            registrant.opt_in_code = opt_in_serializer.dumps(registrant.email)
            registrant.opt_out_code = opt_out_serializer.dumps(registrant.email)
            db.session.commit()

    @classmethod
    def verify_token(cls, token: str, type: str = 'opt_in') -> bool | str:
        if type == 'opt_in':
            serializer = opt_in_serializer
        elif type == 'opt_out':
            serializer = opt_out_serializer
        else:
            raise ValueError('Invalid serializer type. Must be either "opt_in" or "opt_out".')

        try:
            email = serializer.loads(token)
        except:
            return False

        if not (registrant := db.session.query(cls).filter_by(email=email).one_or_none()):
            return False

        if type == 'opt_in' and registrant.opt_in_code:
            registrant.opt_in_code = None
            db.session.add(registrant)
            db.session.commit()
            return email
        elif type == 'opt_out':
            db.session.delete(registrant)
            db.session.commit()
            return True

        return False

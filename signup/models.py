from flask import current_app
from sqlalchemy.orm import Session
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

    def generate_keys(self):
        with current_app.app_context():
            self.opt_in_code = opt_in_serializer.dumps(self.email)
            self.opt_out_code = opt_out_serializer.dumps(self.email)
            Session.object_session(self).commit()

    @classmethod
    def verify_token(cls, email: str, token: str, type: str = 'opt_in') -> bool:
        if not (registrant := db.session.query(cls).filter_by(email=email).one_or_none()):
            return False

        if type == 'opt_in':
            serializer = opt_in_serializer
        elif type == 'opt_out':
            serializer = opt_out_serializer
        else:
            raise ValueError('Invalid serializer type. Must be either "opt_in" or "opt_out".')

        with current_app.app_context():
            try:
                token_email = serializer.loads(token)
            except:
                return False

        if token_email == email:
            if type == 'opt_in':
                registrant.opt_in_code = None
                db.session.add(registrant)
            else:
                db.session.delete(registrant)
            db.session.commit()
            return True

        return False

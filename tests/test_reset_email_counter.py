from helpers.reset_email_counter import reset_email_counter
from models import User
from signup import db

pytest_plugins = [
    'tests.test_signup'
]


def test_reset_email_counter(client, registrant):
    reset_email_counter()
    count = db.session.query(User).filter_by(id=registrant.id).one_or_none().opt_ins_sent
    assert count == 0

import tempfile

import pytest

from models import User, EmailLog, EmailType
from signup import create_app, db
from signup.utilities import count_todays_opt_ins_sent


@pytest.fixture(scope='function')
def client():
    with tempfile.NamedTemporaryFile() as db_file:
        additional_config = {
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///' + db_file.name,
            'TESTING': True,
        }
        app = create_app(additional_config)
        with app.app_context():
            yield app.test_client()


@pytest.fixture(scope='function')
def registrant(client):
    client.post('/', data={'email': 'test@cosmanaut.com'})
    return db.session.query(User).filter_by(email='test@cosmanaut.com').one_or_none()


def test_homepage(client):
    rv = client.get('/')
    assert rv.status_code == 200


def test_registration(client):
    rv = client.post('/', data={'email': 'test@cosmanaut.com'})
    assert b'Confirmation email has been sent to' in rv.data
    registrant = db.session.query(User).filter_by(email='test@cosmanaut.com').one_or_none()
    assert registrant
    assert registrant.opt_in_code

    email_log = db.session.query(EmailLog).filter_by(user=registrant).one_or_none()
    assert email_log.type_id == EmailType.OPT_IN.value
    assert email_log.status_code == 202

    assert count_todays_opt_ins_sent(registrant) == 1



def test_repeat_confirmations(client, registrant):
    rv = client.post('/', data={'email': 'test@cosmanaut.com'})
    assert b'Re-sending confirmation email.' in rv.data

    assert count_todays_opt_ins_sent(registrant) == 2


def test_excessive_confirmations(client, registrant):
    for n in range(5):
        client.post('/', data={'email': 'test@cosmanaut.com'})
    rv = client.post('/', data={'email': 'test@cosmanaut.com'})
    assert b'Please wait until tomorrow' in rv.data

    assert count_todays_opt_ins_sent(registrant) == 5


def test_already_registered(client, registrant):
    registrant.opt_in_code = None
    db.session.commit()
    rv = client.post('/', data={'email': 'test@cosmanaut.com'})
    assert b'This email address is already registered.' in rv.data


def test_confirm_registration(client, registrant):
    token = registrant.opt_in_code
    rv = client.get(f'/confirm/{token}')
    assert b'Your registration has been confirmed' in rv.data
    assert not registrant.opt_in_code


def test_not_registered(client):
    rv = client.get('/confirm/a', follow_redirects=True)
    assert b'This email address has not been registered.' in rv.data

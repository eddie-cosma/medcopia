import tempfile

import pytest

from models import User
from signup import create_app, db


@pytest.fixture(scope='function')
def client():
    with tempfile.NamedTemporaryFile() as db_file:
        test_config = {
            'SERVER_NAME': 'localhost:5000',
            'PREFERRED_URL_SCHEME': 'http',
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///' + db_file.name,
            'MAIL_SERVER': '',
            'MAIL_PORT': 0,
            'MAIL_USERNAME': '',
            'MAIL_PASSWORD': '',
            'MAIL_DEFAULT_SENDER': 'Medcopia Shortage Alerts <test@example.com>',
            'MAIL_PER_DAY_MAX': 2,
            'RECAPTCHA_SITE_KEY': '6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI',
            'RECAPTCHA_SECRET_KEY': '6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe',
            'SECRET_KEY': 'test',
            'TESTING': True,
        }
        app = create_app(test_config)
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
    assert registrant.opt_out_code
    assert registrant.opt_ins_sent == 1


def test_repeat_confirmations(client, registrant):
    rv = client.post('/', data={'email': 'test@cosmanaut.com'})
    assert b'Re-sending confirmation email.' in rv.data


def test_excessive_confirmations(client, registrant):
    client.post('/', data={'email': 'test@cosmanaut.com'})
    rv = client.post('/', data={'email': 'test@cosmanaut.com'})
    assert b'Please wait until tomorrow' in rv.data


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


def test_unsubscribe(client, registrant):
    token = registrant.opt_out_code
    rv = client.get(f'/unsubscribe/{token}')
    assert b'You have been successfully unsubscribed' in rv.data
    assert not db.session.query(User).filter_by(id=registrant.id).one_or_none()

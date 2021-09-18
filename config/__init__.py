import json
import os
from pathlib import Path

ROOT = Path(__file__).parent.parent.absolute()

config = {
    'ROOT': ROOT,
    'SECRET_KEY': 'dev',
    'PREFERRED_URL_SCHEME': 'http',
    'SERVER_NAME': 'localhost:5000',
    'SQLALCHEMY_TRACK_MODIFICATIONS': False,
    'SQLALCHEMY_DATABASE_URI': 'sqlite:///' + str(ROOT / 'instance/data.sqlite'),
    'MAIL_SERVER': '',  # must use SSL (not STARTTLS)
    'MAIL_PORT': 465,  # SSL port
    'MAIL_USERNAME': '',
    'MAIL_PASSWORD': '',
    'MAIL_DEFAULT_SENDER': '',
    'MAIL_PER_DAY_MAX': 5,
    'RECAPTCHA_SITE_KEY': '',
    'RECAPTCHA_SECRET_KEY': '',
}

if os.path.exists(ROOT / 'instance/config.json') and os.getenv('TESTING', 'False') == 'False':
    with open(ROOT / 'instance/config.json') as f:
        config.update(json.load(f))
elif os.path.exists(ROOT / 'instance/test_config.json') and os.getenv('TESTING', 'False') == 'True':
    with open(ROOT / 'instance/test_config.json') as f:
        config.update(json.load(f))

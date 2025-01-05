"""Configuration module for the Medcopia package.

This exports config, a dict of configuration key-value pairs. Defaults are
defined here. Defaults can be overridden by exporting environment variables
prior to running the application.
"""

import os
from pathlib import Path

ROOT = Path(__file__).parent.parent.absolute()

# Default configuration
config = {
    'ROOT': ROOT,
    'SECRET_KEY': 'dev',
    'PREFERRED_URL_SCHEME': 'http',
    'SERVER_NAME': 'localhost:5000',
    'SQLALCHEMY_TRACK_MODIFICATIONS': False,
    'SQLALCHEMY_DATABASE_URI': 'sqlite:///' + str(ROOT / 'instance/data.sqlite'),
    'MAIL_DEFAULT_SENDER': '',
    'MAIL_ALERT_TEMPLATE': '',
    'MAIL_CONFIRM_TEMPLATE': '',
    'MAIL_DEFAULT_ASM_GROUP': 0,
    'RECAPTCHA_SITE_KEY': '',
    'RECAPTCHA_SECRET_KEY': '',
    'SENDGRID_API_KEY': '',
    'TESTING': False,
}

# Override the defaults with environment variables
for key, value in os.environ.items():
    if key in config.keys():
        config[key] = value

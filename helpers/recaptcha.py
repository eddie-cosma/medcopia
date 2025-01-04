import requests
from flask import request, current_app

from config import config


def verify_recaptcha(token: str) -> bool:
    """Validate the provided reCAPTCHA token.

    Functionality based on the `reCAPTCHA specification
    <https://developers.google.com/recaptcha/docs/display>`_.

    :param token: the token provided from the user request.
    :return: ``True`` if the token is valid, ``False`` otherwise.
    """

    if config.get('TESTING'):
        return True

    recaptcha_url = 'https://www.google.com/recaptcha/api/siteverify'
    recaptcha_secret_key = current_app.config['RECAPTCHA_SECRET_KEY']
    payload = {
        'secret': recaptcha_secret_key,
        'response': token,
        'remoteip': request.remote_addr,
    }
    response = requests.post(recaptcha_url, data=payload)
    if response.status_code == 200:
        return response.json()['success']

    return False

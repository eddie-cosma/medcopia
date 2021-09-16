from flask import request, current_app
import requests


def verify_recaptcha(token: str) -> bool:
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

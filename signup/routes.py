from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app

from models import User
from helpers.email import validate
from helpers.recaptcha import verify_recaptcha
from signup import db
from signup.utilities import generate_keys, send_opt_in_confirmation, verify_token

bp = Blueprint('shortage', __name__)


@bp.route('/', methods=['GET', 'POST'])
def signup():
    recaptcha_key = current_app.config['RECAPTCHA_SITE_KEY']
    email = request.form.get('email', None)

    if request.method == 'POST' and email:
        # Confirm reCAPTCHA is successful
        recaptcha_token = request.form.get('g-recaptcha-response')
        if not verify_recaptcha(recaptcha_token):
            flash('Please check the box attesting that you are not a robot.')
            return render_template('signup.html', registrant=None, recaptcha_key=recaptcha_key)

        if registrant := db.session.query(User).filter_by(email=email).one_or_none():
            # Try to send confirmation email if registrant still has an opt-in code
            if registrant.opt_in_code:
                # Ensure we are not hitting the maximum email limit
                max_requests = current_app.config['MAIL_PER_DAY_MAX']
                service_address = current_app.config['MAIL_USERNAME']
                if registrant.opt_ins_sent >= max_requests:
                    flash(f'Only {max_requests} confirmation emails may be sent per day to prevent our emails being \
marked as spam. Please wait until tomorrow or contact {service_address} for assistance.')
                    return render_template('signup.html', registrant=None, recaptcha_key=recaptcha_key)

                # Send confirmation email and increment counter of confirmation messages sent today
                send_opt_in_confirmation(email)
                flash('Re-sending confirmation email. Please check your inbox to confirm this registration.')
            else:
                flash('This email address is already registered.')
            return render_template('signup.html', registrant=None, recaptcha_key=recaptcha_key)

        # If email is valid and not in the database, add it, create confirm/unsub tokens and send confirmation email
        elif validate(email):
            registrant = User(email=email)
            db.session.add(registrant)
            db.session.commit()

            generate_keys(email)
            send_opt_in_confirmation(email)
            return render_template('signup.html', registrant=email, recaptcha_key=recaptcha_key)
        else:
            flash('This email address is invalid.')

    return render_template('signup.html', registrant=None, recaptcha_key=recaptcha_key)


@bp.route('/confirm/<token>', methods=['GET'])
def confirm(token: str):
    if email := verify_token(token, token_type='opt_in'):
        service_address = current_app.config['MAIL_USERNAME']
        return render_template('confirm.html', registrant=email, service_address=service_address)
    else:
        flash('This email address has not been registered.')
        return redirect(url_for('shortage.signup'))


@bp.route('/unsubscribe/<token>', methods=['GET'])
def unsubscribe(token: str):
    if verify_token(token, token_type='opt_out'):
        return render_template('unsubscribe.html')
    else:
        flash('This email address has not been registered.')
        return redirect(url_for('shortage.signup'))

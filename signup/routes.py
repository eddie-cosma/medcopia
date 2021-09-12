from flask import Blueprint, render_template, request, flash, redirect, url_for

from . import db
from .email import validate
from .models import User

bp = Blueprint('shortage', __name__)


@bp.route('/', methods=['GET', 'POST'])
def signup():
    email = request.form.get('email', None)
    if request.method == 'POST' and email:
        if registrant := db.session.query(User).filter_by(email=email).one_or_none():
            if registrant.opt_in_code:
                User.send_opt_in_confirmation(email)
                flash('Re-sending confirmation email. Please check your inbox to confirm this registration.')
            else:
                flash('This email address is already registered.')
        elif validate(email):
            registrant = User(email=email)
            db.session.add(registrant)
            db.session.commit()

            User.generate_keys(email)
            User.send_opt_in_confirmation(email)
        else:
            flash('This email address is invalid.')

    return render_template('signup.html', registrant=email)


@bp.route('/confirm/<token>', methods=['GET'])
def confirm(token: str):
    if email := User.verify_token(token, type='opt_in'):
        return render_template('confirm.html', registrant=email)
    else:
        flash('This email address has not been registered.')
        return redirect(url_for('shortage.signup'))


@bp.route('/unsubscribe/<token>', methods=['GET'])
def unsubscribe(token: str):
    if User.verify_token(token, type='opt_out'):
        return render_template('unsubscribe.html')
    else:
        flash('This email address has not been registered.')
        return redirect(url_for('shortage.signup'))


from flask import Blueprint, render_template, request, flash, redirect, url_for

from . import db
# from .email import ...
from .models import User

bp = Blueprint('shortage', __name__)


@bp.route('/', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template('signup.html', registrant=None)

    elif request.method == 'POST':
        email = request.form.get('email')
        if registrant := db.session.query(User).filter_by(email=email).one_or_none():
            if registrant.opt_in_code:
                # TODO: resend email
                flash('Re-sending confirmation email. Please check your inbox to confirm this registration.')
            else:
                flash('This email address is already registered.')
        else:
            registrant = User(
                email=request.form.get('email')
            )
            db.session.add(registrant)
            db.session.commit()
            registrant.generate_keys()

        return render_template('signup.html', registrant=email)


@bp.route('/confirm/<email>/<token>', methods=['GET'])
def confirm(email: str, token: str):
    if User.verify_token(email, token, type='opt_in'):
        return render_template('confirm.html', registrant=email)
    else:
        flash('This email address has not been registered.')
        return redirect(url_for('shortage.signup'))


@bp.route('/unsubscribe/<email>/<token>', methods=['GET'])
def unsubscribe(email: str, token: str):
    if User.verify_token(email, token, type='opt_out'):
        return render_template('unsubscribe.html')
    else:
        flash('This email address has not been registered.')
        return redirect(url_for('shortage.signup'))


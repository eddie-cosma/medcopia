"""A module for resetting the database counters of newsletter opt-in
confirmation emails sent. Opt-in emails are limited by default to avoid being
marked as abusive. The maximum number of confirmations that may be sent per
day is specified in the ``MAIL_PER_DAY_MAX`` config value.

It is recommended that this be run as a script once daily at a pre-specified
time."""

from models import Session, User


def reset_email_counter(session: Session):
    """Reset the database counter of opt-in emails sent for every user."""
    users = session.query(User).all()
    for user in users:
        user.opt_ins_sent = 0


if __name__ == '__main__':
    session = Session()
    reset_email_counter(session)
    session.commit()
    session.close()

from models import Session, User


def reset_email_counter():
    session = Session()

    users = session.query(User).all()
    for user in users:
        user.opt_ins_sent = 0

    session.commit()
    session.close()


if __name__ == '__main__':
    reset_email_counter()

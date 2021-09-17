from models import Session, User


def reset_email_counter(session: Session):
    users = session.query(User).all()
    for user in users:
        user.opt_ins_sent = 0


if __name__ == '__main__':
    session = Session()
    reset_email_counter(session)
    session.commit()
    session.close()

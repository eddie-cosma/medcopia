from helpers.email import MassMessage
from models import Session, User, Drug

session = Session()

# test_drug = Drug(name='test')
# session.add(test_drug)

test_recipient = session.query(User).filter_by(email='eddie.cosma@gmail.com').all()
# Deleted this template
test_message = MassMessage(test_recipient, 'Test message', 'test.html')
test_message.send_all()

session.commit()
session.close()
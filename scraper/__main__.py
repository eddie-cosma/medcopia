from helpers.email import Recipient, MassMessage
from models import Session, Drug

session = Session()

test_drug = Drug(name='test')
session.add(test_drug)
session.commit()
session.close()

test_recipient = Recipient('eddie.cosma@gmail.com', 'fake_token')
test_recipient2 = Recipient('hello@eddiecosma.com', 'another_fake_token')
test_message = MassMessage([test_recipient], 'Test message', 'test.html')
test_message.send_all()

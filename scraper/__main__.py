"""A module for sending email alerts when the shortage list updates.

When run as a module, does the following:
 * Get the latest version of the ASHP drug shortages list.
 * Compare the current shortages to the (saved) previous shortages.
 * If there are new or resolved shortages, send an alert email to all
   confirmed emails in the database.
"""

import logging
import os

import requests
from bs4 import BeautifulSoup

from config import config
from helpers.emailer import Message
from models import Session, User
from models.delta import ASHPDrug, DrugDelta

logging.basicConfig(level=logging.INFO, format='%(asctime)s : %(levelname)s : %(message)s')

logging.info('Checking ASHP website for updates')
shortage_list_url = 'https://www.ashp.org/drug-shortages/current-shortages/drug-shortages-list?page=CurrentShortages'
shortage_list = requests.get(shortage_list_url)

if shortage_list.status_code != 200:
    logging.error('ASHP website unreachable')
    exit()

ashp_drugs = []
soup = BeautifulSoup(shortage_list.content, 'html.parser')
for link in soup.find(id='1_dsGridView').find_all('a'):
    ashp_drugs.append(ASHPDrug(
        name=link.get_text(),
        detail_url=link.get('href')
    ))

session = Session()
delta = DrugDelta(ashp_drugs, session)
logging.info(f'Found {len(delta.new_shortages)} new and {len(delta.resolved_shortages)} resolved shortages')

# Send emails
if delta.new_shortages or delta.resolved_shortages:
    recipients = session.query(User).filter(User.opt_in_code == None).all()

    template_data = {}
    if delta.new_shortages:
        template_data['new_shortages'] = [
            {
                'name': drug.name,
                'url': drug.url,
            }
            for drug in delta.new_shortages
        ]
    if delta.resolved_shortages:
        template_data['resolved_shortages'] = [
            {
                'name': drug.name,
                'url': drug.url,
            }
            for drug in delta.resolved_shortages
        ]

    message = Message(
        recipients=recipients,
        subject='Medcopia shortage alert',
        template_id=config.get('MAIL_ALERT_TEMPLATE'),
        template_data=template_data,
        session=session,
    )

    if os.getenv('TESTING', 'False') == 'False':
        logging.info('Sending shortage alert emails')
        message.send()
        if message.success:
            logging.info('Emails sent successfully')
            logging.info('Updating local database with most recent shortage list')
            delta.update_database()
        else:
            logging.error('Emails failed to send')

session.commit()
session.close()
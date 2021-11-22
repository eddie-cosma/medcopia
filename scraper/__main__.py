"""A module for sending email alerts when the shortage list updates.

When run as a module, does the following:
 * Get the latest version of the ASHP drug shortages list.
 * Compare the current shortages to the (saved) previous shortages.
 * If there are new or resolved shortages, send an alert email to all
   confirmed emails in the database.
"""

import logging
import os
from datetime import date

import requests
from bs4 import BeautifulSoup

from helpers.emailer import MassMessage
from helpers.reddit import RedditPost
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

# Post to Reddit
if delta.new_shortages:
    logging.info('Posting new shortages to Reddit.')
    for new_shortage in delta.new_shortages:
        reddit_submission = RedditPost(new_shortage)
        reddit_submission.post()

        # Ensure that only one post is submitted if testing
        if os.getenv('TESTING', 'False') == 'True':
            break

# Send emails
if delta.new_shortages or delta.resolved_shortages:
    recipients = session.query(User).filter(User.opt_in_code == None).all()
    today = date.today().strftime('%B %-d, %Y')
    messenger = MassMessage(
        db_session=session,
        recipients=recipients,
        subject='Medcopia shortage alert',
        template_name='alert.html',
        today=today,
        new_shortages=delta.new_shortages,
        resolved_shortages=delta.resolved_shortages,
    )

    if os.getenv('TESTING', 'False') == 'False':
        logging.info('Sending shortage alert emails')
        messenger.send_all()
        logging.info('Updating local database with most recent shortage list')
        delta.update_database()

session.commit()
session.close()
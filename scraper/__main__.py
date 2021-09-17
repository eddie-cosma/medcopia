from datetime import date

import requests
from bs4 import BeautifulSoup

from helpers.email import MassMessage
from models import Session, User
from models.delta import ASHPDrug, DrugDelta

shortage_list_url = 'https://www.ashp.org/drug-shortages/current-shortages/drug-shortages-list?page=CurrentShortages'
shortage_list = requests.get(shortage_list_url)

if shortage_list.status_code != 200:
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

if delta.new_shortages or delta.resolved_shortages:
    recipients = session.query(User).filter(User.opt_in_code == None).all()
    today = date.today().strftime('%B %-d, %Y')
    messenger = MassMessage(
        recipients=recipients,
        subject='Medcopia shortage alert',
        template_name='alert.html',
        today=today,
        new_shortages=delta.new_shortages,
        resolved_shortages=delta.resolved_shortages,
    )
    messenger.send_all()
    delta.update_database()

session.commit()
session.close()
from urllib.parse import urlparse, parse_qs

from models import Session, Drug

ashp_base_detail_url = 'https://www.ashp.org/drug-shortages/current-shortages/drug-shortage-detail.aspx?id='


class ASHPDrug:
    def __init__(self,
                 name: str,
                 drug_id: int = None,
                 detail_url: str = None,
                 ):
        self.name = name
        self.drug_id = drug_id or int(parse_qs(urlparse(detail_url).query).get('id')[0])

    @property
    def url(self):
        return ashp_base_detail_url + str(self.drug_id)


class DrugDelta:
    def __init__(self,
                 ashp_drugs: list[ASHPDrug],
                 db_session: Session,
                 ):
        self._session = db_session

        self.drugs = ashp_drugs

        self.new_shortages = None
        self.resolved_shortages = None
        self.compare_previous()

    def compare_previous(self):
        session = self._session

        ashp_ids = [drug.drug_id for drug in self.drugs]
        local_ids = [x for (x,) in session.query(Drug.id).all()]

        self.new_shortages = [x for x in self.drugs if x.drug_id not in local_ids]
        self.resolved_shortages = [x for x in session.query(Drug).filter(~Drug.id.in_(ashp_ids)).all()]

    def update_database(self):
        session = self._session
        for shortage in self.resolved_shortages:
            session.remove(shortage)
        for shortage in self.new_shortages:
            session.add(Drug(
                id=shortage.drug_id,
                name=shortage.name,
            ))
        session.commit()

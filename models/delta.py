from urllib.parse import urlparse, parse_qs

from models import Session, Drug

ashp_base_detail_url = 'https://www.ashp.org/drug-shortages/current-shortages/drug-shortage-detail.aspx?id='


class ASHPDrug:
    """Represents a drug from the ASHP shortages list."""

    def __init__(self,
                 name: str,
                 drug_id: int = None,
                 detail_url: str = None,
                 ):
        self.name = name
        self.drug_id = drug_id or int(parse_qs(urlparse(detail_url).query).get('id')[0])

    @property
    def url(self):
        """Get the ASHP drug shortages detail url."""
        return ashp_base_detail_url + str(self.drug_id)


class DrugDelta:
    """Represents a comparison between the current ASHP drug shortages list
    and the local database, which is itself a representation of the ASHP
    shortages list at the time of the last update."""

    def __init__(self,
                 ashp_drugs: list[ASHPDrug],
                 db_session: Session,
                 ):
        self._session = db_session

        self.drugs = ashp_drugs

        self.new_shortages = None
        self.resolved_shortages = None
        self._compare_previous()

    def _compare_previous(self):
        """Make the lists of new and resolved shortages."""
        session = self._session

        ashp_ids = [drug.drug_id for drug in self.drugs]
        local_ids = [x for (x,) in session.query(Drug.id).all()]

        self.new_shortages = [x for x in self.drugs if x.drug_id not in local_ids]
        self.resolved_shortages = [x for x in session.query(Drug).filter(~Drug.id.in_(ashp_ids)).all()]

    def update_database(self):
        """Update the local database to reflect the current state of the ASHP
        drug shortages list."""
        session = self._session
        delete_ids = [drug.id for drug in self.resolved_shortages]
        session.query(Drug).filter(Drug.id.in_(delete_ids)).delete()
        for shortage in self.new_shortages:
            session.add(Drug(
                id=shortage.drug_id,
                name=shortage.name,
            ))
        session.commit()

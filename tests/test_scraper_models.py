import pytest

from models import Session, Drug
from models.delta import ASHPDrug, DrugDelta


@pytest.fixture(scope='function')
def session():
    yield Session()
    Session.close_all()


@pytest.fixture(scope='function')
def preexisting_drugs(session):
    drug1 = Drug(
        id=1,
        name='Cefazolin Injection',
    )
    drug2 = Drug(
        id=2,
        name='Ibuprofen Oral Liquid',
    )
    session.add(drug1)
    session.add(drug2)
    session.commit()
    return drug1, drug2


def test_shortage_update(session, preexisting_drugs):
    drug1, drug2 = preexisting_drugs
    new_shortage = ASHPDrug(name='Acetaminophen Tablet', drug_id=3)
    existing_shortage = ASHPDrug(name=drug2.name, drug_id=drug2.id)
    delta = DrugDelta([new_shortage, existing_shortage], session)
    delta.update_database()

    from pprint import pprint
    pprint(session.query(Drug).all())

    # Assert correct drug was identified as new and added to database
    assert delta.new_shortages == [new_shortage]
    assert session.query(Drug).filter_by(id=3).one_or_none().name == 'Acetaminophen Tablet'

    # Assert correct drug was identified as resolved and removed from database
    assert delta.resolved_shortages == [drug1]
    assert not session.query(Drug).filter_by(id=1).one_or_none()

    # Assert drug that did not change is still in the database
    assert session.query(Drug).filter_by(id=2).one_or_none()

import json
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

CURRENT_FOLDER = Path(__file__).parent.resolve()
INSTANCE_FOLDER = CURRENT_FOLDER.parent / 'instance'

with open(INSTANCE_FOLDER / 'config.json', 'r') as f:
    CONFIG = json.load(f)

engine = create_engine('sqlite:////' + str(INSTANCE_FOLDER / 'data.sqlite'))
Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

from .models import User, Drug
Base.metadata.create_all(bind=engine)

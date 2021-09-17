from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from config import config

engine = create_engine(config['SQLALCHEMY_DATABASE_URI'])
Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

from .database import User, Drug
Base.metadata.create_all(bind=engine)

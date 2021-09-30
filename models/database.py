from sqlalchemy import Column, Integer, DateTime, String, func

from models import Base

ashp_base_detail_url = 'https://www.ashp.org/drug-shortages/current-shortages/drug-shortage-detail.aspx?id='


class User(Base):
    """The user model."""

    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    email = Column(String(255), nullable=False, unique=True)
    opt_in_code = Column(String(255), nullable=True)
    opt_out_code = Column(String(255), nullable=True)
    opt_ins_sent = Column(Integer, nullable=False, default=0)
    last_message_time = Column(DateTime(timezone=False), nullable=True)
    created_time = Column(DateTime(timezone=False), nullable=False, server_default=func.now())
    modified_time = Column(DateTime(timezone=False), nullable=True, onupdate=func.now())

    def __repr__(self):
        return f'<Registrant {self.email}>'


class Drug(Base):
    """The drug model."""

    __tablename__ = 'drug'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)

    def __repr__(self):
        return f'<Drug shortage for {self.name}>'

    @property
    def url(self):
        """Get the ASHP drug shortages detail url based on :attr:`id` value.

        This presumes that stored :attr:`id` values are synchronized between
        the local database and the ASHP website.
        """
        return ashp_base_detail_url + str(self.id)

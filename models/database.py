from sqlalchemy import Column, Integer, DateTime, String, func

from models import Base

ashp_base_detail_url = 'https://www.ashp.org/drug-shortages/current-shortages/drug-shortage-detail.aspx?id='


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    email = Column(String(255), nullable=False, unique=True)
    opt_in_code = Column(String(255), nullable=True)
    opt_out_code = Column(String(255), nullable=True)
    opt_ins_sent = Column(Integer, nullable=False, default=0)
    last_message_time = Column(DateTime(timezone=False), nullable=True)
    created_time = Column(DateTime(timezone=False), nullable=False, server_default=func.now())
    modified_time = Column(DateTime(timezone=False), nullable=True, onupdate=func.now())


class Drug(Base):
    __tablename__ = 'drug'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)

    @property
    def url(self):
        return ashp_base_detail_url + str(self.id)

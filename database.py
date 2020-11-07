from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy import Column, TIMESTAMP, String, Integer

from datetime import datetime
from contextlib import contextmanager

import json

Base = declarative_base()
engine = create_engine('sqlite:///custodial.sqlite')
Session = sessionmaker(bind=engine)

@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    session = Session()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()

class SpendingLimits(Base):
    __tablename__ = "botprofile"

    id = Column(Integer, primary_key=True)
    user = Column(String(64))
    bot_secret = Column(String(64))
    token = Column(String(16))
    limit = Column(Integer) # 6 decimals

    added = Column(TIMESTAMP, nullable=False)
    updated = Column(TIMESTAMP, nullable=False)

    @classmethod
    def getsert(cls, session, user, bot_secret, token):
        data = session.query(SpendingLimits).\
            filter(SpendingLimits.user == user).\
            filter(SpendingLimits.bot_secret == bot_secret).\
            first()
        if not data:
            data = SpendingLimits(
                user=user,
                bot_secret=bot_secret,
                token=token,
                limit=0,
                added=datetime.utcnow(),
                updated=datetime.utcnow()
            )
            session.add(data)
        return data

    def claim(self, amount):
        if self.token == "DAI":
            amount /= 1000000000000
        if self.limit < amount:
            return False
        self.limit -= amount
        self.updated=datetime.utcnow()
        return True

    def get_user_limit(self):
        return self.limit / 1000000

    def get_code_imit(self):
        if self.token == "USDC":
            return self.limit
        return self.limit * 1000000000000

    def new_limit(self, new_limit):
        self.limit = new_limit * 1000000
        self.updated=datetime.utcnow()

def main():
    Base.metadata.create_all(engine)

if __name__ == "__main__":
    main()
# SQLAlchemy table definitions
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from database import Base

class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    user_name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    
class Account(Base):
    __tablename__ = "accounts"

    account_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    balance = Column(Integer)

class Transaction(Base):
    __tablename__ = "transactions"

    transaction_id = Column(Integer, primary_key=True, index=True)
    amount = Column(Integer)
    date_time = Column(DateTime)
    from_account_id = Column(Integer, ForeignKey("accounts.account_id"))
    to_account_id = Column(Integer, ForeignKey("accounts.account_id"))
    status = Column(String)
# Pydantic request/response shapes
from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    email: str

class AccountCreate(BaseModel):
    user_id: int
    balance: float

class TransactionCreate(BaseModel):
    from_account_id: int
    to_account_id: int
    amount: float
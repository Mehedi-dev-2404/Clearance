from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal
import models, schemas

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/accounts")
def create_account(account: schemas.AccountCreate, db: Session = Depends(get_db)):
    # Check if user exists
    user = db.query(models.User).filter(models.User.user_id == account.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Create new account
    new_account = models.Account(user_id=account.user_id, balance=account.balance)
    db.add(new_account)
    db.commit()
    db.refresh(new_account)

    return {"account_id": new_account.account_id, "balance": new_account.balance}
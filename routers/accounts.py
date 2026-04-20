from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal
import models, schemas
from sqlalchemy import or_

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

@router.get("/accounts/{id}/history")
def id_history(id: int, db: Session = Depends(get_db)):
    get_transactions = db.query(models.Transaction).filter(
    or_(
        models.Transaction.from_account_id == id,
        models.Transaction.to_account_id == id
    )).all()

    return get_transactions

@router.get("/accounts/{id}/balance")
def get_balance(id: int, db: Session = Depends(get_db)):
    account = db.query(models.Account).filter(
    models.Account.account_id == id
    ).first()
    
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    return {"account_id": id, "balance": account.balance}
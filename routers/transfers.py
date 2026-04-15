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

@router.post("/transfer")
def transfer_funds(transfer: schemas.TransactionCreate, db: Session = Depends(get_db)):
    sender = db.query(models.Account).filter(models.Account.account_id == transfer.from_account_id).first()
    receiver = db.query(models.Account).filter(models.Account.account_id == transfer.to_account_id).first()

    if not sender or not receiver:
        raise HTTPException(status_code=404, detail="Sender or receiver account not found")

    if sender.balance < transfer.amount:
        raise HTTPException(status_code=400, detail="Insufficient funds")

    sender.balance -= transfer.amount
    receiver.balance += transfer.amount

    transaction = models.Transaction(
        from_account_id=transfer.from_account_id,
        to_account_id=transfer.to_account_id,
        amount=transfer.amount,
        status="pending"
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    return {"transaction_id": transaction.transaction_id, "status": "success"}
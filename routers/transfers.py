# Your /transfer endpoints
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
    # Fetch sender and receiver accounts
    sender = db.query(models.Account).filter(models.Account.account_id
 == transfer.sender_id).first()
    receiver = db.query(models.Account).filter(models.Account.account_id == transfer.receiver_id).first()

    if not sender or not receiver:
        raise HTTPException(status_code=404, detail="Sender or receiver account not found")

    if sender.balance < transfer.amount:
        raise HTTPException(status_code=400, detail="Insufficient funds")

    # Perform the transfer
    sender.balance -= transfer.amount
    receiver.balance += transfer.amount

    # Create a transaction record
    transaction = models.Transaction(
        sender_id=sender.id,
        receiver_id=receiver.id,
        amount=transfer.amount
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    return {"transaction_id": transaction.id, "status": "success"}
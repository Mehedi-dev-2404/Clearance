# FastAPI app entry point

from fastapi import FastAPI
from database import engine, Base
from routers import transfers
from routers import accounts
from routers import user

app = FastAPI()
Base.metadata.create_all(bind=engine)
app.include_router(transfers.router)
app.include_router(accounts.router)
app.include_router(user.router)

@app.get("/")
def root():
    return {"status": "Clearance is live"}
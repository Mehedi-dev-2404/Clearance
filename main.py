# FastAPI app entry point

from fastapi import FastAPI
from database import engine, Base
from routers import transfers

app = FastAPI()
Base.metadata.create_all(bind=engine)
app.include_router(transfers.router)

@app.get("/")
def root():
    return {"status": "Clearance is live"}
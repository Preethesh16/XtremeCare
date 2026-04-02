from fastapi import FastAPI
from api.routes import patients, logs

app = FastAPI(
    title="XtremeCare Backend",
    version="1.0.0"
)

app.include_router(patients.router)
app.include_router(logs.router)

@app.get("/")
def root():
    return {"message": "XtremeCare API running"}
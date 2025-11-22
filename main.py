import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError
from typing import Any, Dict

from database import db, create_document
from schemas import Inquiry

app = FastAPI(title="Resplend API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Resplend backend is running"}

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response: Dict[str, Any] = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set",
        "database_name": "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set",
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["connection_status"] = "Connected"
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:80]}"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"

    return response

@app.post("/inquiry")
def create_inquiry(payload: dict):
    """Accept website inquiries and store them in MongoDB."""
    try:
        inquiry = Inquiry(**payload)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors())

    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")

    doc_id = create_document("inquiry", inquiry)
    return {"status": "ok", "id": doc_id}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

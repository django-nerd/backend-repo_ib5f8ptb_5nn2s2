import os
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from database import db, create_document, get_documents
from schemas import MenuItem, Special, GalleryImage, Testimonial, ContactMessage, Reservation, AnalyticsEvent

app = FastAPI(title="Éclat Dining API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Éclat Dining API running"}

# Utility to map model to collection name

def collection_name(model_cls):
    return model_cls.__name__.lower()

# Public content endpoints
@app.get("/api/menu", response_model=List[MenuItem])
def get_menu(category: Optional[str] = None, featured: Optional[bool] = None):
    flt = {}
    if category:
        flt["category"] = category
    if featured is not None:
        flt["featured"] = featured
    items = get_documents(collection_name(MenuItem), flt)
    # Convert Mongo docs to pydantic-friendly dicts
    cleaned = []
    for it in items:
        it.pop("_id", None)
        cleaned.append(MenuItem(**it))
    return cleaned

@app.get("/api/specials", response_model=List[Special])
def get_specials(active: Optional[bool] = True):
    flt = {"active": True} if active else {}
    docs = get_documents(collection_name(Special), flt)
    out = []
    for d in docs:
        d.pop("_id", None)
        out.append(Special(**d))
    return out

@app.get("/api/gallery", response_model=List[GalleryImage])
def get_gallery():
    docs = get_documents(collection_name(GalleryImage))
    out = []
    for d in docs:
        d.pop("_id", None)
        out.append(GalleryImage(**d))
    return out

@app.get("/api/testimonials", response_model=List[Testimonial])
def get_testimonials():
    docs = get_documents(collection_name(Testimonial), {"featured": True})
    out = []
    for d in docs:
        d.pop("_id", None)
        out.append(Testimonial(**d))
    return out

# Forms
@app.post("/api/contact")
def submit_contact(payload: ContactMessage):
    ref = create_document(collection_name(ContactMessage), payload)
    return {"status": "ok", "reference": ref}

class ReservationRequest(Reservation):
    pay_now: Optional[bool] = False

@app.post("/api/reservations")
def submit_reservation(payload: ReservationRequest):
    # Payment placeholder integration (Stripe/Razorpay)
    payment_reference = None
    if payload.pay_now:
        # In real integration, create payment intent/order here and return client secret/order id
        payment_reference = f"PAY-{int(datetime.utcnow().timestamp())}"
    data = payload.model_dump()
    data["payment_reference"] = payment_reference
    ref = create_document(collection_name(Reservation), data)
    return {"status": "ok", "reference": ref, "payment_reference": payment_reference}

# Lightweight analytics
@app.post("/api/analytics")
def track_analytics(event: AnalyticsEvent, request: Request):
    data = event.model_dump()
    data["ip"] = request.client.host if request.client else None
    data["received_at"] = datetime.utcnow().isoformat()
    ref = create_document(collection_name(AnalyticsEvent), data)
    return {"status": "ok", "ref": ref}

# Admin utilities (no auth for demo; add auth before production)
class MenuImport(BaseModel):
    items: List[MenuItem]

@app.post("/admin/import-menu")
def import_menu(payload: MenuImport):
    if db is None:
        raise HTTPException(500, detail="Database not available")
    coll = db[collection_name(MenuItem)]
    docs = []
    for it in payload.items:
        d = it.model_dump()
        d["created_at"] = datetime.utcnow()
        d["updated_at"] = datetime.utcnow()
        docs.append(d)
    if docs:
        coll.insert_many(docs)
    return {"message": f"Imported {len(docs)} menu items"}

@app.get("/admin/reservations")
def list_reservations(limit: int = 100):
    docs = get_documents(collection_name(Reservation), {}, limit)
    out = []
    for d in docs:
        d.pop("_id", None)
        out.append(d)
    # Sort latest first if timestamps exist
    out.sort(key=lambda x: x.get("created_at", datetime.min), reverse=True)
    return out

# Health check + DB check
@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

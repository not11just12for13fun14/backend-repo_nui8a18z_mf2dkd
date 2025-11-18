import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bson.objectid import ObjectId

from database import db, create_document, get_documents
from schemas import Career, SavedCareer, TestQuestion, TestSubmission, TestResult, Counselor, ContactMessage

app = FastAPI(title="CareerPath API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "CareerPath API running"}

# Utility
class CareerCard(BaseModel):
    id: str
    icon: str
    name_en: str
    name_te: str
    short_desc_en: str
    short_desc_te: str
    salary_min: int
    salary_max: int
    education: str
    job_type: str
    field: str


def to_str_id(doc):
    doc["id"] = str(doc.pop("_id"))
    return doc

# Seed minimal data if empty
@app.on_event("startup")
def seed_data():
    if db is None:
        return
    if db["career"].count_documents({}) == 0:
        sample = [
            Career(
                icon="Stethoscope",
                name_en="Nurse",
                name_te="నర్స్",
                short_desc_en="Care for patients in hospitals and clinics.",
                short_desc_te="ఆస్పత్రుల్లో రోగుల సంరక్షణ.",
                salary_min=15000,
                salary_max=40000,
                education="Diploma/B.Sc Nursing",
                job_type="Government",
                field="Healthcare",
                skills=["Compassion", "Communication", "Basic Medical"],
                tags=["helping", "people"],
                growth_path_en=["Nursing Student", "Staff Nurse", "Head Nurse"],
                growth_path_te=["విద్యార్థి నర్స్", "స్టాఫ్ నర్స్", "హెడ్ నర్స్"],
            ).model_dump(),
            Career(
                icon="Wrench",
                name_en="Electrician",
                name_te="ఎలక్ట్రిషియన్",
                short_desc_en="Install and repair electrical systems.",
                short_desc_te="విద్యుత్ వ్యవస్థల ఏర్పాటు మరియు మరమ్మత్తులు.",
                salary_min=12000,
                salary_max=35000,
                education="ITI Electrician / Apprenticeship",
                job_type="Private",
                field="Trades",
                skills=["Problem Solving", "Safety", "Tools"],
                tags=["fixing", "hands-on"],
                growth_path_en=["Apprentice", "Technician", "Contractor"],
                growth_path_te=["శిక్షణార్థి", "టెక్నీషియన్", "కాంట్రాక్టర్"],
            ).model_dump(),
            Career(
                icon="PenTool",
                name_en="Teacher",
                name_te="ఉపాధ్యాయుడు",
                short_desc_en="Teach students and guide learning.",
                short_desc_te="విద్యార్థులకు బోధించడం మరియు మార్గనిర్దేశం.",
                salary_min=18000,
                salary_max=50000,
                education="B.Ed / D.Ed",
                job_type="Government",
                field="Education",
                skills=["Communication", "Patience"],
                tags=["teaching", "helping"],
                growth_path_en=["Assistant Teacher", "Teacher", "Headmaster"],
                growth_path_te=["సహాయ ఉపాధ్యాయుడు", "ఉపాధ్యాయుడు", "హెడ్‌మాస్టర్"],
            ).model_dump(),
        ]
        db["career"].insert_many(sample)

# Public endpoints
@app.get("/api/careers", response_model=List[CareerCard])
def list_careers(q: Optional[str] = None, field: Optional[str] = None, edu: Optional[str] = None):
    if db is None:
        return []
    query = {}
    if q:
        query["$or"] = [
            {"name_en": {"$regex": q, "$options": "i"}},
            {"name_te": {"$regex": q, "$options": "i"}},
            {"field": {"$regex": q, "$options": "i"}},
            {"tags": {"$in": [q]}}
        ]
    if field:
        query["field"] = field
    if edu:
        query["education"] = {"$regex": edu, "$options": "i"}

    docs = list(db["career"].find(query).limit(60))
    return [CareerCard(**to_str_id(d)) for d in docs]

@app.get("/api/careers/{career_id}")
def career_detail(career_id: str):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    doc = db["career"].find_one({"_id": ObjectId(career_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Not found")
    return to_str_id(doc)

@app.post("/api/save", status_code=201)
def save_career(item: SavedCareer):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    existing = db["savedcareer"].find_one({"user_id": item.user_id, "career_id": item.career_id})
    if existing:
        return {"status": "exists"}
    _id = create_document("savedcareer", item)
    return {"status": "ok", "id": _id}

@app.get("/api/saved/{user_id}")
def list_saved(user_id: str):
    if db is None:
        return []
    docs = list(db["savedcareer"].find({"user_id": user_id}))
    for d in docs:
        d["id"] = str(d.pop("_id"))
    return docs

@app.delete("/api/saved/{user_id}/{saved_id}")
def delete_saved(user_id: str, saved_id: str):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    db["savedcareer"].delete_one({"_id": ObjectId(saved_id), "user_id": user_id})
    return {"status": "deleted"}

# Test questions (5 steps minimal)
@app.get("/api/test/questions", response_model=List[TestQuestion])
def get_questions():
    if db is None:
        # Fallback static if no DB
        return [
            TestQuestion(step=1, question_en="Which activity do you enjoy most?", question_te="మీకు ఎక్కువగా ఇష్టమయ్యే చర్య ఏది?", options=[
                {"key": "fix", "label_en": "Fixing things", "label_te": "వస్తువులు సరిచేయడం", "icon": "Wrench"},
                {"key": "help", "label_en": "Helping people", "label_te": "జనాలకు సహాయం చేయడం", "icon": "Heart"},
                {"key": "teach", "label_en": "Teaching others", "label_te": "ఇతరులకు బోధించడం", "icon": "BookOpen"},
                {"key": "create", "label_en": "Drawing/creative", "label_te": "డ్రాయింగ్/సృజనాత్మక", "icon": "PenTool"},
            ]),
        ]
    docs = list(db["testquestion"].find({}).sort("step", 1))
    if not docs:
        # seed 5 simple steps
        seeds = [
            TestQuestion(step=1, question_en="Which activity do you enjoy most?", question_te="మీకు ఎక్కువగా ఇష్టమయ్యే చర్య ఏది?", options=[
                {"key": "fix", "label_en": "Fixing things", "label_te": "వస్తువులు సరిచేయడం", "icon": "Wrench"},
                {"key": "help", "label_en": "Helping people", "label_te": "జనాలకు సహాయం చేయడం", "icon": "Heart"},
                {"key": "teach", "label_en": "Teaching others", "label_te": "ఇతరులకు బోధించడం", "icon": "BookOpen"},
                {"key": "create", "label_en": "Drawing/creative", "label_te": "డ్రాయింగ్/సృజనాత్మక", "icon": "PenTool"},
            ]),
            TestQuestion(step=2, question_en="Where do you prefer to work?", question_te="మీకు ఏ పనిస్థలం ఇష్టం?", options=[
                {"key": "out", "label_en": "Outdoors", "label_te": "బయట", "icon": "Trees"},
                {"key": "in", "label_en": "Indoors", "label_te": "లోపల", "icon": "Home"},
                {"key": "both", "label_en": "Both", "label_te": "రెండూ", "icon": "Sun"},
            ]),
            TestQuestion(step=3, question_en="What matters more?", question_te="మీకు ఎక్కువ ముఖ్యమైనది?", options=[
                {"key": "pay", "label_en": "High salary", "label_te": "ఎక్కువ జీతం", "icon": "IndianRupee"},
                {"key": "secure", "label_en": "Job security", "label_te": "ఉద్యోగ భద్రత", "icon": "Shield"},
                {"key": "impact", "label_en": "Helping society", "label_te": "సమాజానికి సహాయం", "icon": "HandHeart"},
            ]),
            TestQuestion(step=4, question_en="Your strength?", question_te="మీ బలం?", options=[
                {"key": "hands", "label_en": "Hands-on work", "label_te": "చేతులతో పని", "icon": "Hammer"},
                {"key": "people", "label_en": "People skills", "label_te": "మనుషులతో సామర్థ్యం", "icon": "Users"},
                {"key": "logic", "label_en": "Logic/Math", "label_te": "తార్కికం/గణితం", "icon": "FunctionSquare"},
                {"key": "art", "label_en": "Art/Design", "label_te": "కళ/డిజైన్", "icon": "Palette"},
            ]),
            TestQuestion(step=5, question_en="Preferred employer?", question_te="ఇష్టమైన ఉద్యోగం?", options=[
                {"key": "govt", "label_en": "Government", "label_te": "ప్రభుత్వ", "icon": "Building2"},
                {"key": "private", "label_en": "Private", "label_te": "ప్రైవేట్", "icon": "Briefcase"},
                {"key": "self", "label_en": "Self-employed", "label_te": "స్వయం ఉపాధి", "icon": "Store"},
            ]),
        ]
        db["testquestion"].insert_many([s.model_dump() for s in seeds])
        docs = list(db["testquestion"].find({}).sort("step", 1))
    for d in docs:
        d.pop("_id", None)
    return docs

@app.post("/api/test/submit", response_model=TestResult)
def submit_test(payload: TestSubmission):
    # Simple rule mapping for demo: map answers to tags/fields
    tag_map = {
        "fix": ["hands-on", "Trades"],
        "help": ["helping", "Healthcare"],
        "teach": ["teaching", "Education"],
        "create": ["creative", "Design"],
        "logic": ["logic", "Engineering"],
        "govt": ["Government"],
        "private": ["Private"],
        "self": ["Self-employed"],
    }
    filters = []
    for a in payload.answers:
        if a in tag_map:
            val = tag_map[a]
            if len(val) == 1:
                filters.append({"job_type": val[0]})
            else:
                filters.append({"$or": [{"tags": {"$in": [val[0]]}}, {"field": val[1]}]})
    query = {"$and": filters} if filters else {}

    docs = list(db["career"].find(query).limit(6)) if db else []
    ids = [str(d.get("_id")) for d in docs]
    if db:
        create_document("testresult", {"user_id": payload.user_id or "guest", "answers": payload.answers, "recommended_ids": ids})
    return TestResult(user_id=payload.user_id, recommended_ids=ids)

@app.get("/api/counselors", response_model=List[Counselor])
def counselors():
    if db is None:
        return []
    docs = list(db["counselor"].find({}).limit(100))
    if not docs:
        seeds = [
            Counselor(name="Anitha R.", phone="90000 11111", district="Anantapur"),
            Counselor(name="Srinivas K.", phone="90000 22222", district="Kurnool"),
        ]
        db["counselor"].insert_many([s.model_dump() for s in seeds])
        docs = list(db["counselor"].find({}).limit(100))
    for d in docs:
        d.pop("_id", None)
    return docs

@app.post("/api/contact")
def contact(msg: ContactMessage):
    if db:
        create_document("contactmessage", msg)
    return {"status": "received"}

# Health + DB test
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
            response["database_url"] = "✅ Configured"
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

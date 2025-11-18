"""
Database Schemas for CareerPath

Each Pydantic model here maps to a MongoDB collection whose name is the lowercase
of the class name. Example: Career -> "career" collection.
"""
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Literal

# Core domain models
class Career(BaseModel):
    icon: str = Field(..., description="Lucide icon name for the career")
    name_en: str = Field(..., description="Career name (English)")
    name_te: str = Field(..., description="Career name (Telugu)")
    short_desc_en: str = Field(..., description="Short description (English)")
    short_desc_te: str = Field(..., description="Short description (Telugu)")
    salary_min: int = Field(..., ge=0, description="Minimum monthly salary (INR)")
    salary_max: int = Field(..., ge=0, description="Maximum monthly salary (INR)")
    education: str = Field(..., description="Required education path")
    job_type: Literal['Government','Private','Self-employed','Mixed'] = 'Mixed'
    field: str = Field(..., description="Field/industry e.g., Healthcare, Engineering")
    skills: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list, description="Keywords for matching")
    growth_path_en: List[str] = Field(default_factory=list, description="Simple timeline labels (English)")
    growth_path_te: List[str] = Field(default_factory=list, description="Simple timeline labels (Telugu)")

class SavedCareer(BaseModel):
    user_id: str = Field(..., description="Logical user id or 'guest-<device>'")
    career_id: str = Field(..., description="ObjectId string for the career")

class TestQuestion(BaseModel):
    step: int = Field(..., ge=1)
    question_en: str
    question_te: str
    options: List[dict] = Field(..., description="List of {key, label_en, label_te, icon}")

class TestSubmission(BaseModel):
    user_id: Optional[str] = None
    answers: List[str] = Field(..., description="Selected option keys per step")

class TestResult(BaseModel):
    user_id: Optional[str] = None
    recommended_ids: List[str]

class Counselor(BaseModel):
    name: str
    phone: str
    district: str

class ContactMessage(BaseModel):
    name: str
    email: EmailStr
    message: str

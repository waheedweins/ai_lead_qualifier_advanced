from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


class LeadCreate(BaseModel):
    name: Optional[str] = None
    email: EmailStr
    phone: Optional[str] = None
    source: Optional[str] = "manual"
    title: Optional[str] = None
    address: Optional[str] = None
    website: Optional[str] = None


class LeadResponse(BaseModel):
    id: int
    name: Optional[str] = None
    email: str
    phone: Optional[str] = None
    source: Optional[str] = None
    status: str
    ai_score: int
    ai_reason: Optional[str] = None
    title: Optional[str] = None
    address: Optional[str] = None
    website: Optional[str] = None
    apollo_enriched: bool = False
    outreach_sent: bool = False
    outreach_channel: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class LeadScoreResponse(BaseModel):
    id: int
    email: str
    ai_score: int
    ai_reason: Optional[str] = None
    decision: str

    model_config = {"from_attributes": True}


class LeadStatsResponse(BaseModel):
    total: int
    hot: int
    cold: int
    avg_score: float
    processed: int
    new_leads: int
    outreach_sent: int
    apollo_enriched: int

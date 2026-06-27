from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from src.app.core.database import Base


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=True)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, nullable=True, index=True)
    source = Column(String, nullable=True)           # google_maps | apollo | manual
    status = Column(String, default="new", nullable=False)   # new | processing | processed | failed
    ai_score = Column(Integer, default=0, nullable=False)
    ai_reason = Column(Text, nullable=True)          # Gemini's explanation
    title = Column(String, nullable=True)            # job title or business category
    address = Column(String, nullable=True)
    website = Column(String, nullable=True)          # website URL if found
    website_summary = Column(Text, nullable=True)    # Tavily enrichment summary
    apollo_enriched = Column(Boolean, default=False) # whether Apollo data was fetched
    outreach_sent = Column(Boolean, default=False)   # whether outreach was triggered
    outreach_channel = Column(String, nullable=True) # whatsapp | email
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    agent_runs = relationship("AgentRun", back_populates="lead", cascade="all, delete-orphan")

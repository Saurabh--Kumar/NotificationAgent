from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from uuid import UUID
from app.models.enums import CampaignStatus


class CampaignBase(BaseModel):
    company_id: UUID
    company_name: str = Field(..., max_length=255)
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    theme: str = Field(..., max_length=100)
    category: str = Field(..., max_length=100)
    brand_voice: Optional[str] = None
    target_audience: Optional[str] = None
    industry: Optional[str] = Field(None, max_length=100)
    start_date: datetime
    end_date: datetime


class CampaignCreate(CampaignBase):
    pass


class CampaignUpdate(BaseModel):
    company_name: Optional[str] = Field(None, max_length=255)
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    theme: Optional[str] = Field(None, max_length=100)
    category: Optional[str] = Field(None, max_length=100)
    brand_voice: Optional[str] = None
    target_audience: Optional[str] = None
    industry: Optional[str] = Field(None, max_length=100)
    status: Optional[CampaignStatus] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class CampaignInDBBase(CampaignBase):
    id: UUID
    status: CampaignStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class Campaign(CampaignInDBBase):
    pass


class CampaignWithSessions(Campaign):
    notification_sessions: List["NotificationSession"] = []

    class Config:
        from_attributes = True

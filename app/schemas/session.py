from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from uuid import UUID
from app.models.enums import NotificationSessionStatus


class SessionCreate(BaseModel):
    topic: Optional[str] = Field(
        None,
        description="Topic for the notification generation session"
    )
    campaign_id: UUID = Field(
        ...,
        description="ID of the campaign this session is associated with"
    )
    company_id: UUID = Field(
        ...,
        description="ID of the company this session belongs to"
    )
    admin_id: UUID = Field(
        ...,
        description="ID of the admin who initiated the session"
    )


class SessionBase(SessionCreate):
    id: UUID = Field(..., description="Unique identifier for the session")
    status: NotificationSessionStatus = Field(
        ...,
        description="Current status of the session"
    )
    created_at: datetime = Field(..., description="When the session was created")
    updated_at: datetime = Field(
        ...,
        description="When the session was last updated"
    )

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


class Session(SessionBase):
    all_suggestions: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="All notification suggestions generated in this session"
    )
    selected_suggestions: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Suggestions selected by the admin"
    )
    conversation_history: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Full conversation history for this session"
    )


class SessionResponse(BaseModel):
    session_id: UUID = Field(..., description="ID of the created session")
    status: str = Field(..., description="Current status of the session")

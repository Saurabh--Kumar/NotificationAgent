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

    model_config = {"from_attributes": True}


class Session(SessionBase):
    all_suggestions: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="All notification suggestions generated in this session. Each suggestion contains 'id', 'notification_text', 'news_headline', and 'status'."
    )
    selected_suggestions: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Suggestions selected by the admin. Each suggestion contains 'id', 'notification_text', 'news_headline', and 'status'."
    )
    conversation_history: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Full conversation history for this session"
    )


class SessionResponse(BaseModel):
    session_id: UUID = Field(..., description="ID of the created session")
    status: str = Field(..., description="Current status of the session")


class FeedbackRequest(BaseModel):
    feedback: str = Field(..., description="Feedback text to append to conversation history")


class PublishRequest(BaseModel):
    selected_suggestion_ids: List[str] = Field(
        ...,
        description="List of suggestion IDs to publish"
    )

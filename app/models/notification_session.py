from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import Column, String, Text, JSON, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from ..db.session import Base
from .enums import NotificationSessionStatus

class NotificationSession(Base):
    """
    Represents a notification generation session.
    """
    __tablename__ = "notification_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    admin_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    status = Column(Enum(NotificationSessionStatus), default=NotificationSessionStatus.PROCESSING, nullable=False)
    
    # Session metadata
    topic = Column(String(255), nullable=True)  # Current topic for notification generation
    current_topic_version = Column(Integer, default=1)  # Tracks topic changes for feedback loops
    
    # Notification data
    all_suggestions = Column(JSON, default=list)  # All suggestions generated so far
    selected_suggestions = Column(JSON, default=list)  # Suggestions selected by admin
    rejected_suggestions = Column(JSON, default=list)  # Suggestions explicitly rejected by admin
    
    # Session tracking
    conversation_history = Column(JSON, default=list)  # Full conversation history
    feedback_history = Column(JSON, default=list)  # History of feedback provided by admin
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_feedback_at = Column(DateTime, nullable=True)  # When the last feedback was provided
    
    # Foreign key to associate with campaign
    campaign_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("campaigns.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Relationship with Campaign (many-to-one)
    campaign = relationship("Campaign", back_populates="notification_sessions")
    
    def add_suggestions(self, suggestions: List[str]) -> None:
        if not self.all_suggestions:
            self.all_suggestions = []
        self.all_suggestions.extend(suggestions)
        self.updated_at = datetime.utcnow()
    
    def update_selections(self, selected_indices: List[int]) -> None:
        if not self.all_suggestions:
            return
            
        self.selected_suggestions = [
            self.all_suggestions[i] 
            for i in selected_indices 
            if 0 <= i < len(self.all_suggestions)
        ]
        self.updated_at = datetime.utcnow()
    
    def add_feedback(self, feedback: str) -> None:
        if not self.feedback_history:
            self.feedback_history = []
            
        self.feedback_history.append({
            'timestamp': datetime.utcnow().isoformat(),
            'feedback': feedback,
            'topic_version': self.current_topic_version
        })
        self.last_feedback_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def change_topic(self, new_topic: str) -> None:
        self.topic = new_topic
        self.current_topic_version += 1
        self.updated_at = datetime.utcnow()

    def __repr__(self):
        return f"<NotificationSession(id={self.id}, status={self.status}, company_id={self.company_id})>"

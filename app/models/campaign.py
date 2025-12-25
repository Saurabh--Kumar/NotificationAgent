from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum, Uuid
from sqlalchemy.orm import relationship

import uuid

from ..db.session import Base
from .enums import CampaignStatus

class Campaign(Base):

    __tablename__ = "campaigns"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    company_id = Column(Uuid(as_uuid=True), nullable=False, index=True)

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    theme = Column(String(100), nullable=False)
    category = Column(String(100), nullable=False)
    status = Column(Enum(CampaignStatus), default=CampaignStatus.DRAFT, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationship with NotificationSession (one-to-many)
    notification_sessions = relationship(
        "NotificationSession", 
        back_populates="campaign",
        foreign_keys="[NotificationSession.campaign_id]",
        primaryjoin="Campaign.id == NotificationSession.campaign_id",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Campaign(id={self.id}, name='{self.name}', status={self.status})>"

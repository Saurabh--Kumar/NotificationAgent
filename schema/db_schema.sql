-- Initial database schema for Notification Agent
-- This script creates all necessary tables, constraints, and indexes

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create campaigns table
CREATE TABLE IF NOT EXISTS campaigns (
    campaign_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    theme VARCHAR(100) NOT NULL,
    category VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'DRAFT' CHECK (status IN ('DRAFT', 'ACTIVE', 'PAUSED', 'COMPLETED', 'CANCELLED')),
    start_date TIMESTAMP WITH TIME ZONE NOT NULL,
    end_date TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT end_date_after_start_date CHECK (end_date > start_date)
);

-- Create notification_sessions table
CREATE TABLE IF NOT EXISTS notification_sessions (
    session_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_id UUID NOT NULL,
    company_id UUID NOT NULL,
    admin_id UUID NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'PROCESSING' CHECK (status IN ('PROCESSING', 'AWAITING_REVIEW', 'COMPLETED', 'FAILED')),
    topic VARCHAR(255),
    current_topic_version INTEGER DEFAULT 1,
    
    -- Notification data
    all_suggestions JSONB DEFAULT '[]'::jsonb,
    selected_suggestions JSONB DEFAULT '[]'::jsonb,
    rejected_suggestions JSONB DEFAULT '[]'::jsonb,
    
    -- Session tracking
    conversation_history JSONB DEFAULT '[]'::jsonb,
    feedback_history JSONB DEFAULT '[]'::jsonb,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_feedback_at TIMESTAMP WITH TIME ZONE,
    
    -- Foreign key constraint
    CONSTRAINT fk_notification_session_campaign 
        FOREIGN KEY (campaign_id) 
        REFERENCES campaigns(campaign_id)
        ON DELETE CASCADE
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_campaigns_company_id ON campaigns(company_id);
CREATE INDEX IF NOT EXISTS idx_campaigns_status ON campaigns(status);
CREATE INDEX IF NOT EXISTS idx_notification_sessions_campaign_id ON notification_sessions(campaign_id);
CREATE INDEX IF NOT EXISTS idx_notification_sessions_company_id ON notification_sessions(company_id);
CREATE INDEX IF NOT EXISTS idx_notification_sessions_admin_id ON notification_sessions(admin_id);
CREATE INDEX IF NOT EXISTS idx_notification_sessions_status ON notification_sessions(status);

-- Add comments for better documentation
COMMENT ON TABLE campaigns IS 'Stores marketing campaign information';
COMMENT ON COLUMN campaigns.status IS 'Current status of the campaign: DRAFT, ACTIVE, PAUSED, COMPLETED, or CANCELLED';

COMMENT ON TABLE notification_sessions IS 'Tracks notification generation sessions';
COMMENT ON COLUMN notification_sessions.status IS 'Current status of the notification session: PROCESSING, AWAITING_REVIEW, COMPLETED, or FAILED';

-- Timestamp updates are managed by the application

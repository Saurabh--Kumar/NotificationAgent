from typing import Optional
import uuid
from uuid import UUID
from sqlalchemy.orm import Session as DBSession

from app.celery_app import celery_app
from app.db.session import SessionLocal
from app.crud import session as crud_session
from app.models.enums import NotificationSessionStatus



@celery_app.task(name="app.tasks.run_agent_task")

def run_agent_task(session_id: str) -> dict:
    db: DBSession = SessionLocal()
    
    try:
        session_uuid = UUID(session_id)
        db_session = crud_session.get_notification_session(db, session_id=session_uuid)
        
        if not db_session:
            return {
                "status": "error",
                "message": f"Session {session_id} not found"
            }
        
        # Call LangGraph agent to generate notifications
        from app.agent import generate_notifications
        from langchain_core.messages import AIMessage

        topic = db_session.topic or "general notifications"
        company_id = str(db_session.company_id) if db_session.company_id else None

        try:
            agent_messages = generate_notifications(topic=topic, company_id=company_id)
            
            # Extract suggestions and conversation history from agent messages
            suggestions = []
            conversation = []
            
            for msg in agent_messages:
                if isinstance(msg, AIMessage):
                    # Parse notification suggestions from agent response
                    # Split content into individual suggestions (assuming one per line)
                    suggestion_texts = [line.strip() for line in msg.content.split("\n") if line.strip()]
                    for text in suggestion_texts:
                        suggestions.append({
                            "id": str(uuid.uuid4()),
                            "text": text,
                            "status": "pending"
                        })
                # Add to conversation history
                role = "assistant" if isinstance(msg, AIMessage) else "user"
                conversation.append({"role": role, "content": msg.content})

            # Update session with generated suggestions and conversation history
            db_session.all_suggestions = suggestions
            db_session.conversation_history = conversation
            db.commit()

            # Update session status to AWAITING_REVIEW
            crud_session.update_session_status(
                db=db,
                db_session=db_session,
                status=NotificationSessionStatus.AWAITING_REVIEW
            )

        except Exception as agent_error:
            # Update status to FAILED if agent execution fails
            crud_session.update_session_status(
                db=db,
                db_session=db_session,
                status=NotificationSessionStatus.FAILED
            )
            raise agent_error
        
        return {
            "status": "success",
            "session_id": session_id,
            "message": "Agent task placeholder executed"
        }
        
    except Exception as e:
        if db_session:
            crud_session.update_session_status(
                db=db,
                db_session=db_session,
                status=NotificationSessionStatus.FAILED
            )
        
        return {
            "status": "error",
            "session_id": session_id,
            "message": str(e)
        }
    
    finally:
        db.close()

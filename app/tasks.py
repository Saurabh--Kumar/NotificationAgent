import json
import logging
import traceback
from typing import Optional
import uuid
from uuid import UUID
from sqlalchemy.orm import Session as DBSession

from app.db.session import SessionLocal
from app.crud import session as crud_session
from app.models.enums import NotificationSessionStatus


def run_agent_task(session_id: str) -> dict:
    db: DBSession = SessionLocal()
    db_session = None
    
    try:
        session_uuid = UUID(session_id)
        db_session = crud_session.get_notification_session(db, session_id=session_uuid)
        
        if not db_session:
            logging.info(f"module=app.tasks method=run_agent_task message=Session {session_id} not found")
            return {
                "status": "error",
                "message": f"Session {session_id} not found"
            }
        
        # Call LangGraph agent to generate notifications
        from app.agent import generate_notifications

        topic = db_session.topic or "general notifications"
        company_id = str(db_session.company_id) if db_session.company_id else None
        
        logging.info(f"module=app.tasks method=run_agent_task message=Generating notifications for topic: {topic}")

        try:
            suggestions = generate_notifications(topic=topic, company_id=company_id)

            logging.info(f"module=app.tasks method=run_agent_task message=Generated {len(suggestions)} suggestions")
            logging.info(f"module=app.tasks method=run_agent_task message=Suggestions type: {type(suggestions)}, first item type: {type(suggestions[0]) if suggestions else 'N/A'}")
            logging.info(f"module=app.tasks method=run_agent_task message=Suggestions sample: {str(suggestions[:2])}")

            # Convert list of pairs [notification_text, headline] to list of suggestion objects
            suggestions_list = []
            for pair in suggestions:
                try:
                    if isinstance(pair, list) and len(pair) >= 2:
                        suggestions_list.append({
                            "id": str(uuid.uuid4()),
                            "notification_text": str(pair[0]),
                            "news_headline": str(pair[1]),
                            "status": "pending"
                        })
                    elif isinstance(pair, dict):
                        suggestions_list.append({
                            "id": str(uuid.uuid4()),
                            "notification_text": str(pair.get("notification_text", pair.get("text", ""))),
                            "news_headline": str(pair.get("news_headline", "")),
                            "status": "pending"
                        })
                    else:
                        suggestions_list.append({
                            "id": str(uuid.uuid4()),
                            "notification_text": str(pair),
                            "news_headline": "",
                            "status": "pending"
                        })
                except Exception as item_error:
                    logging.warning(f"module=app.tasks method=run_agent_task message=Failed to process suggestion item {pair}: {str(item_error)}")
                    continue
            
            # Add to conversation history
            conversation = [
                {"role": "user", "content": f"Generate notifications for topic: {topic}"},
                {"role": "assistant", "content": suggestions_list}
            ]

            # Update session with generated suggestions and conversation history
            db_session.all_suggestions = suggestions_list
            db_session.conversation_history = conversation
            db.commit()

            # Update session status to AWAITING_REVIEW
            crud_session.update_session_status(
                db=db,
                db_session=db_session,
                status=NotificationSessionStatus.AWAITING_REVIEW
            )
            
            logging.info(f"module=app.tasks method=run_agent_task message=Session {session_id} status updated to AWAITING_REVIEW")

        except Exception as agent_error:
            # Update status to FAILED if agent execution fails
            crud_session.update_session_status(
                db=db,
                db_session=db_session,
                status=NotificationSessionStatus.FAILED
            )
            logging.error(f"module=app.tasks method=run_agent_task message=Agent error: {str(agent_error)}")
            logging.error(f"module=app.tasks method=run_agent_task message=Agent error type: {type(agent_error).__name__}")
            logging.error(f"module=app.tasks method=run_agent_task message=Agent traceback: {traceback.format_exc()}")
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
        
        logging.error(f"module=app.tasks method=run_agent_task message=Task error: {str(e)}")
        
        return {
            "status": "error",
            "session_id": session_id,
            "message": str(e)
        }
    
    finally:
        db.close()

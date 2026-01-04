# **AI Notification Generation Agent: Design Document**

## 1\. Overview

### 1.1. Goal

To create a scalable, multi-tenant, and highly available service that allows B2C enterprise customers to generate timely, context-aware, and catchy notifications for their end-users. The system will leverage a Large Language Model (LLM) agent to craft notification suggestions based on real-time news, company campaigns, and brand identity. A human-in-the-loop (HITL) workflow is central to the design, ensuring business admins have full control over the final message.

### 1.2. Core Principles

  * **Scalability:** The architecture must handle numerous concurrent admin sessions from different businesses without performance degradation.
  * **Statelessness:** The core AI agent will be stateless to simplify scaling and improve reliability. All state will be managed by the backend application.
  * **Separation of Concerns:** A clear distinction will be maintained between the API/state management layer (FastAPI), the AI/logic layer (LangGraph), and the data persistence layer.
  * **Asynchronicity:** Long-running tasks, like LLM generation, will be handled asynchronously to ensure the API remains responsive.

-----

## 2\. System Architecture

The system is designed around a decoupled, service-oriented architecture.

### 2.1. Architectural Diagram

```
+-----------+         +-------------------------+      +-----------------------+
| Admin UI  | <-----> |   FastAPI Backend API   |      | LangGraph Agent       |
| (Web App) |         |  (REST Endpoints)       |      | (Stateless Generator) |
+-----------+         +-------------------------+      +-----------+-----------+
                            |           ^                        |
                            |           | (Results)              | (Tools)
                            v           |                        v
+---------------------------+-----------+------------------------+-----------+
|   Asynchronous Task Queue (Celery & Redis)                     |           |
+----------------------------------------------------------------+           |
|                           |                                    |           |
|                           v                                    v           v
|   +-----------------------+------------------+     +-----------+-----------+
|   |   Database (PostgreSQL)                  |     | Third-Party Services  |
|   | - Session State                          |     | - News API            |
|   | - Company/Campaign Info                  |     | - Customer's Notif. Svc|
|   +------------------------------------------+     +-----------------------+
```

### 2.2. Component Breakdown

  * **Admin UI:** A web-based front end where the business admin interacts with the system. It initiates requests, displays suggestions, captures feedback, and triggers the final publish action.
  * **FastAPI Backend:** The central nervous system of the application. It exposes REST APIs, manages user authentication, handles session state, orchestrates asynchronous tasks, and interacts with the database. **It does not contain the core LLM logic.**
  * **Asynchronous Task Queue (Celery & Redis):** Used to offload the time-consuming process of running the LangGraph agent. This prevents API requests from timing out and allows the system to handle a high volume of concurrent requests. Redis serves as the message broker.
  * **LangGraph Agent:** A stateless service responsible for the "thinking." It takes a snapshot of the current state (chat history, company data, news articles) and generates notification suggestions. Its only job is to process information and return a result.
  * **Database (PostgreSQL):** Persists all long-term data, including session information, conversation history, **company profiles, and campaign details.**
  * **Third-Party Services:**
      * **News API:** External service to fetch real-time news articles.
      * **Notification Service:** The customer's internal service that is ultimately responsible for dispatching the notifications to end-users.

-----

## 3\. API Endpoints (FastAPI)

All endpoints are protected and require `company_id` and `admin_id` for authorization and multi-tenancy.

### `POST /api/v1/notification-sessions`

  * **Description:** Initiates a new notification generation session.
  * **Request Body:**
    ```json
    {
      "topic": "Sports" // Optional
    }
    ```
  * **Workflow:**
    1.  Create a new `Session` record in the database with a unique `session_id` and a status of `PROCESSING`.
    2.  Dispatch an asynchronous task (e.g., `run_agent_task`) with the `session_id`.
    3.  Return an immediate `202 Accepted` response.
  * **Response Body (202):**
    ```json
    {
      "session_id": "uuid-v4-string",
      "status": "PROCESSING"
    }
    ```

### `GET /api/v1/notification-sessions/{session_id}`

  * **Description:** Pollable endpoint for the UI to check the status and retrieve results of a session.
  * **Path Parameter:** `session_id` (string).
  * **Workflow:**
    1.  Fetch the `Session` record from the database using the `session_id`.
    2.  Return the session's current status and any generated suggestions.
  * **Response Body (200):**
    ```json
    {
      "session_id": "uuid-v4-string",
      "status": "AWAITING_REVIEW", // or "PROCESSING", "COMPLETED"
      "suggestions": [
        "🔥 Score big this weekend with our 50% off sports gear sale!",
        "Don't get left on the sidelines! Major deals on all team jerseys now."
      ],
      "conversation_history": [
        {"role": "user", "content": "Generate notifications about Sports"},
        {"role": "assistant", "content": "Here are 5 suggestions..."}
      ]
    }
    ```

### `POST /api/v1/notification-sessions/{session_id}/feedback`

  * **Description:** Allows the admin to provide feedback or ask for modifications.
  * **Path Parameter:** `session_id` (string).
  * **Request Body:**
    ```json
    {
      "message": "These are good, but can you make them funnier and add emojis?"
    }
    ```
  * **Workflow:**
    1.  Load the session and its `conversation_history` from the database.
    2.  Append the new admin message to the history.
    3.  Update the session status to `PROCESSING`.
    4.  Dispatch another `run_agent_task` with the `session_id`.
    5.  Return an immediate `202 Accepted` response.
  * **Response Body (202):**
    ```json
    {
      "session_id": "uuid-v4-string",
      "status": "PROCESSING"
    }
    ```

### `POST /api/v1/notification-sessions/{session_id}/publish`

  * **Description:** Sends the final, admin-approved notifications. **This endpoint does not interact with the agent.**
  * **Path Parameter:** `session_id` (string).
  * **Request Body:**
    ```json
    {
      "notifications": [
        "🔥 Score big this weekend with our 50% off sports gear sale! ⚽️",
        "Don't get left on the sidelines! Major deals on all team jerseys now. 👕"
      ]
    }
    ```
  * **Workflow:**
    1.  Validate the request.
    2.  Make a secure, server-to-server call to the customer's registered Notification Service webhook/API.
    3.  On success, update the session status to `COMPLETED`.
    4.  Return a `200 OK` response.
  * **Response Body (200):**
    ```json
    {
      "status": "SUCCESS",
      "message": "2 notifications have been queued for delivery."
    }
    ```

-----

## 4\. Agent Design (LangGraph)

The agent is designed to be a pure, stateless function that executes within an asynchronous task.

### 4.1. Agent State (`TypedDict`)

This structure is passed into the agent at the start of every run.

```python
from typing import List, TypedDict, Optional

class AgentState(TypedDict):
    company_id: str
    conversation_history: List[dict]
    # Data gathered by tools
    company_profile: Optional[dict]
    active_campaigns: Optional[List[dict]]
    news_articles: Optional[List[dict]]
    # Final output
    generated_suggestions: List[str]
    error_message: Optional[str] # For handling tool failures
```

### 4.2. Agent Tools

The agent only has tools for information gathering.

  * `fetch_company_profile(company_id: str) -> dict`: Retrieves the company's profile (e.g., brand voice, target audience, industry) from the **application's database**.
  * `fetch_active_campaigns(company_id: str) -> List[dict]`: Fetches currently running campaigns from the **application's database**.
      * **Implementation Note:** This tool will execute a SQL query similar to:
        ```sql
        SELECT theme, category, start_date, end_date
        FROM campaigns
        WHERE company_id = :company_id
          AND NOW() BETWEEN start_date AND end_date;
        ```
      * If the query returns no results, the tool will return an empty list `[]`. The agent must be prompted to handle this case gracefully.
  * `get_news_articles(topic: str, count: int = 5) -> List[dict]`: Fetches `count` articles from the News API for a given `topic`.

### 4.3. Agent Graph Flow

The graph orchestrates the agent's reasoning process.

```
      (START)
         |
         v
+--------------------+
|   Analyze Request  | --> (Is new info needed?) --YES--+
| (Router Node)      |                                  |
+--------------------+                                  |
         | (NO)                                         |
         v                                              v
+--------------------+                        +--------------------+
| Generate/Refine    |                        |   Gather Info      |
| Suggestions (LLM)  |                        | (Parallel Tool Use)|
+--------------------+                        +--------------------+
         |                                              |
         | <--------------------------------------------+
         v
       (END)
```

1.  **START:** The agent is invoked with the `AgentState` populated from the database by the Celery worker.
2.  **Analyze Request (Router):** An LLM call examines the *last message* in `conversation_history`.
      * If it's the first turn or requests a new topic (e.g., "now give me some about movies"), it routes to the `Gather Info` node.
      * If it's a refinement request (e.g., "make it funnier"), it bypasses information gathering and routes directly to the `Generate Suggestions` node.
3.  **Gather Info (Conditional Node):** Invokes the necessary tools in parallel. For example, `fetch_company_profile` and `fetch_active_campaigns` are always called, while `get_news_articles` is called only if a topic is specified or inferred. Tool outputs are added to the `AgentState`.
4.  **Generate Suggestions (LLM Node):** The core LLM call. It receives a comprehensive prompt containing:
      * The full `conversation_history`.
      * The `company_profile` (for tone and voice).
      * The list of `active_campaigns` (for context).
      * The fetched `news_articles`.
      * A directive to generate 5 catchy notification messages.
5.  **END:** The final state, with the `generated_suggestions` field populated, is returned by the agent function. The Celery worker then takes this result and updates the database.

-----

## 5\. Data Models (PostgreSQL)

```sql
CREATE TYPE session_status AS ENUM ('PROCESSING', 'AWAITING_REVIEW', 'COMPLETED', 'FAILED');

CREATE TABLE notification_sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id VARCHAR(255) NOT NULL,
    admin_id VARCHAR(255) NOT NULL,
    status session_status NOT NULL,
    conversation_history JSONB, -- Stores the array of role/content messages
    generated_suggestions JSONB, -- Stores the last list of suggestions
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for efficient session lookups
CREATE INDEX idx_sessions_company_admin ON notification_sessions (company_id, admin_id);

-- NEW TABLE for Campaigns
CREATE TABLE campaigns (
    campaign_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id VARCHAR(255) NOT NULL, -- Foreign key to a 'companies' table
    theme TEXT NOT NULL,
    category VARCHAR(255),
    start_date TIMESTAMP WITH TIME ZONE NOT NULL,
    end_date TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for efficient lookups of active campaigns per company
CREATE INDEX idx_active_campaigns ON campaigns (company_id, start_date, end_date);
```

-----

## 6\. Asynchronous Task Processing (Celery)

### `tasks.py`

```python
from celery import Celery
from .agent import run_langgraph_agent # Your agent logic
from .database import get_session, update_session_results, update_session_status

app = Celery('tasks', broker='redis://localhost:6379/0')

@app.task
def run_agent_task(session_id: str):
    # 1. Fetch current session state from DB
    session = get_session(session_id)
    if not session:
        # Handle error: session not found
        return

    # 2. Construct the initial AgentState
    initial_state = {
        "company_id": session.company_id,
        "conversation_history": session.conversation_history,
        # ... other fields are initially empty
    }

    # 3. Run the agent graph
    try:
        final_state = run_langgraph_agent(initial_state)
        # 4. Update the database with the results
        update_session_results(
            session_id,
            final_state["generated_suggestions"],
            final_state["conversation_history"] # Persist the agent's response
        )
        update_session_status(session_id, "AWAITING_REVIEW")
    except Exception as e:
        # 5. Handle any errors during agent execution
        update_session_status(session_id, "FAILED")
        # Log the error `e`
```

-----

## 7\. Scalability and Performance

  * **Horizontal Scaling:** The FastAPI backend and Celery workers are stateless and can be scaled horizontally by running more instances behind a load balancer.
  * **Database Performance:** Proper indexing on `session_id`, `company_id`, and campaign date ranges is crucial. For extremely high-volume scenarios, consider using a database read replica.
  * **Connection Pooling:** Use connection pooling (like PgBouncer) to manage database connections efficiently from multiple API/worker instances.
  * **API Responsiveness:** The asynchronous architecture ensures the API remains fast and responsive, never blocking on long-running LLM calls.

-----

## 8\. Edge Cases and Error Handling

  * **News API Failure:** The `get_news_articles` tool should have robust error handling (e.g., try/except blocks, retries with exponential backoff). If it fails, the agent should be able to proceed without news articles and inform the user (e.g., "I couldn't fetch the latest news, but here are some suggestions based on your active campaigns.").
  * **LLM Failure/Bad Output:** If the LLM call fails or returns malformed JSON, the agent task should fail gracefully. The session status in the database will be updated to `FAILED`, and the UI can display a generic "An error occurred, please try again" message.
  * **Empty Results:** If no campaigns or relevant news are found, the agent should be prompted to generate more generic, evergreen notifications suitable for the company's profile.
  * **Long Admin Delay:** Because the agent is stateless, it doesn't matter if an admin waits five minutes or five days to provide feedback. When they do, the API simply loads the session state from the database and starts a new, fresh agent run.
  * **Race Conditions:** If an admin rapidly submits multiple feedback messages, the system should process them sequentially. Using a task queue naturally enforces this. The UI should disable the "submit" button while a request is `PROCESSING`.

-----

## 9\. Security Considerations

  * **Authentication & Authorization:** All API endpoints must be protected. An API gateway or middleware should validate JWTs or other auth tokens to identify the `admin_id` and their associated `company_id`.
  * **Input Sanitization:** Sanitize all user input (e.g., the `topic` and `message` fields) to prevent injection attacks.
  * **Prompt Injection:** The LLM prompt must be carefully constructed to mitigate the risk of prompt injection. Frame the prompt with clear system instructions and demarcate user-provided content clearly (e.g., using XML tags like `<user_feedback>`).
  * **Secrets Management:** API keys for the News API and other services must be stored securely (e.g., in HashiCorp Vault, AWS Secrets Manager) and not hardcoded in the application.
  * **Multi-tenancy:** All database queries **must** be scoped with `WHERE company_id = ?` to ensure one company's admin cannot access another company's data.
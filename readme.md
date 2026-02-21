# 🏥 Appointment Booking Agent

A LangGraph + Streamlit implementation of the multi-step appointment booking agent with human-in-the-loop review.

## Architecture

```
Email Trigger
     │
     ▼
[Node 1] Scan & Parse Email
     │  → extracts: name, age, email, requested_date
     ▼
[Node 2] Check Availability (Scheduling System Plugin)
     │
     ├── Slot Found ──────────────────────────────────────────────────┐
     │                                                                 │
     └── No Slot Found                                                 │
              │                                                        │
              ▼                                                        │
         [Node 3] Draft Email with New Proposed Slots                 │
              │                                                        │
              ▼                                                        │
         [Human Review] John reviews & approves                        │
              │                                                        │
              ▼                                                        │
         [Send Email] Email Plugin sends to Patient X                 │
              │                                                        │
              ▼                                                        │
         [Node 4] Receive Patient Response (Trigger)                  │
              │                                                        │
              └───────────────────────────────────────────────────────┤
                                                                       ▼
                                                              [Node 5] Book Appointment
                                                                   + Notify Patient
                                                                   + Notify Practitioner
```

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the Streamlit app
streamlit run app.py
```

## File Structure

```
appointment_agent/
├── agent.py        # LangGraph graph definition + all nodes
├── app.py          # Streamlit UI
├── requirements.txt
└── README.md
```

## Key Components

### `agent.py`
- **`AgentState`** — TypedDict defining all state fields passed between nodes
- **Node functions** — one Python function per graph node
- **`build_graph()`** — assembles the LangGraph `StateGraph` with conditional routing
- **Mock plugins** — `scheduling_system_check()`, `scheduling_system_book()`, `send_email()`

### `app.py`
- Dark-themed Streamlit UI
- Live workflow progress visualization
- Tabs: Summary, Agent Logs, Draft Email
- Run history tracking

## Extending for Production

### Replace Mock Plugins with Real Integrations

```python
# scheduling_system_check — connect to Google Calendar / Calendly / custom DB
import googleapiclient.discovery
def scheduling_system_check(requested_date):
    service = googleapiclient.discovery.build('calendar', 'v3', credentials=creds)
    events = service.events().list(...).execute()
    return extract_free_slots(events)

# send_email — use SendGrid / AWS SES / Gmail API
import sendgrid
def send_email(to, subject, body):
    sg = sendgrid.SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY'))
    message = Mail(from_email='clinic@example.com', to_emails=to, ...)
    sg.send(message)
```

### Use an LLM for Email Parsing (Node 1)

```python
from langchain_anthropic import ChatAnthropic

def scan_and_parse_email(state):
    llm = ChatAnthropic(model="claude-3-haiku-20240307")
    response = llm.invoke(f"""
    Extract from this email:
    - patient_name
    - patient_age  
    - patient_email
    - requested_date
    
    Email: {state['raw_email']}
    
    Return as JSON.
    """)
    parsed = json.loads(response.content)
    return {**state, **parsed}
```

### Real Human-in-the-Loop with LangGraph Interrupts

```python
# Add interrupt_before to pause execution
graph.compile(
    checkpointer=memory,
    interrupt_before=["send_proposed_slots_email"]  # pause here for human approval
)

# Resume after human approves via API/UI:
graph.invoke(None, config, command=Command(resume={"approved": True}))
```

### Add LangSmith Tracing

```python
import os
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = "your-key"
```

## State Schema

| Field | Type | Description |
|-------|------|-------------|
| `raw_email` | str | Original email text |
| `patient_name` | str | Parsed patient name |
| `patient_age` | int | Parsed patient age |
| `patient_email` | str | Patient's email address |
| `requested_date` | str | Patient's preferred date |
| `available_slots` | List[str] | Slots from scheduling system |
| `selected_slot` | str | Confirmed appointment slot |
| `human_approved` | bool | Whether John approved draft |
| `draft_email` | str | Draft email to patient |
| `proposed_slots` | List[str] | New slots offered to patient |
| `status` | str | Current workflow status |
| `iteration` | int | Loop iteration counter |
| `logs` | List[str] | Step-by-step audit trail |


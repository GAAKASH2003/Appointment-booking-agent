
import json
import random
from datetime import datetime, timedelta
from typing import TypedDict, Literal, Optional, List
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from datetime import datetime, timedelta
from pydantic import BaseModel
from typing import Literal
import re


llm = ChatOllama(model="llama3.1")

class AgentState(TypedDict):
    # Input
    raw_email: str
    patient_name: str
    patient_age: Optional[int]
    patient_email: str
    requested_date: Optional[str]
    requested_time: str
    # Availability
    available_slots: List[str]
    selected_slot: Optional[str]
    # Human-in-loop
    human_approved: bool
    human_feedback: Optional[str]
    # Draft email
    draft_email: Optional[str]
    confirmation_email: Optional[str]
    proposed_slots: List[str]
    # Patient response
    patient_response: Optional[str]
    # Status tracking
    status: str
    iteration: int
    logs: List[str]



# ---- Structured output for the email ----
class AppointmentEmail(BaseModel):
    to: str
    subject: str
    body: str

class SlotResponse(BaseModel):
    accepted: bool
    body: str

class ParseEmail(BaseModel):
    patient_name: str
    patient_age:int
    patient_email:str
    requested_date:str
    requested_time:str


# ---- Structured output ----
class AvailabilityResult(BaseModel):
    slot_found: bool
    matched_slot: Optional[str]   # if slot_found = True
    proposed_slots: List[str]     # if slot_found = False, suggest alternatives


class ConfirmationEmail(BaseModel):
    subject: str
    body: str

class DraftEmail(BaseModel):
    subject: str
    body: str

# ---- Patient X Agent ----
def PatientXAgent(
    action: Literal["write_email", "respond_to_slots"],
    patient_info: dict|None = None,
    context: str|None = None,
):
    today = datetime.now().strftime("%Y-%m-%d")
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

    if action == "write_email":
        prompt = f"""
        You are Patient X. Write a professional appointment request email to a doctor.
        
        Patient details:
        - Name: select patientX or patientY or patientZ
        - fromEmail: patient@gmail.com
        - toEmail: doctor@gmail.com
        - Age: select age between 20 to 60
        
        Request a date of either today ({today}) or tomorrow ({tomorrow}) give a particular date.
        Preferred time: select any time between 9:00 AM and 11:00 PM give a particular time .
        
        Return structured output with all fields filled.
        """
        structured_llm = llm.with_structured_output(AppointmentEmail)
        response = structured_llm.invoke(prompt)
        print("Generated Email:", response)
        return response

    elif action == "respond_to_slots":
       
        
        prompt = f"""
        You are Patient X. A doctor's office has proposed new appointment slots 
        because your original request didn't match availability.
        
        Patient details:
        - Name: {patient_info['name']}
        - Age: {patient_info['age']}
        - Context: {context}
        
        Review the slots. If any work for the patient , 
        accept the best one and write a confirmation reply with requested slot in the format example: "I confirm the appointment for 2025-01-21 at 2:00 PM. Thank you!".
        strictly choose from the proposed slots in context and do not make up new slots.
        Return structured output.
        """
        structured_llm = llm.with_structured_output(SlotResponse)
        response = structured_llm.invoke(prompt)
        print("Generated Slot Response:", response)
        return response

def scan_and_parse_email(state: AgentState) -> dict:   # ← state, not AgentState
    raw_email_body = state["raw_email"]
    status = state["status"]
    if status!="patient_accepted":
         
            prompt = f"""
            You are an email parser for a medical scheduling system.
            Extract the following fields from the patient's email below.
            
            Email:
            ---
            {raw_email_body}
            ---
            
            Rules:
            - requested_date: format as YYYY-MM-DD. If not mentioned, use today's date.
            - requested_time: format as HH:MM AM/PM. If not mentioned, use "09:00 AM".
            - patient_age: extract as positive integer if not present take 25 as default.
            - patient_email: extract from email body or headers if not present take it as <name_of_patient>@gmail.com.
            """

            structured_llm = llm.with_structured_output(ParseEmail)
            response: ParseEmail = structured_llm.invoke(prompt)

            log_entry = f"[scan_and_parse_email] Parsed email for {response.patient_name}"

            # ← Return dict to update AgentState
            return {
                "patient_name": response.patient_name,
                "patient_age": response.patient_age,
                "patient_email": response.patient_email,
                "requested_date": response.requested_date,
                "requested_time": response.requested_time,
                "status": "email_parsed",
                "logs": state.get("logs", []) + [log_entry]
            }
    else:
        # If we are here, it means we are processing a patient response email with proposed slots
        log_entry = f"[scan_and_parse_email] Processing patient response email with context: {state['patient_response']}"
        prompt = f"""
            You are an email parser for a medical scheduling system.
            Extract the following fields from the patient's email below.
            
            Email:
            ---
            {state['patient_response']}
            ---
            
            Rules:
            - requested_date: format as YYYY-MM-DD. If not mentioned, use today's date.
            - requested_time: format as HH:MM AM/PM. If not mentioned, use "09:00 AM".
          
            """

        structured_llm = llm.with_structured_output(ParseEmail)
        response: ParseEmail = structured_llm.invoke(prompt)

        log_entry = f"[scan_and_parse_email] Parsed response email for {response.patient_name}"

        # ← Return dict to update AgentState
        return {
            "requested_date": response.requested_date,
            "requested_time": response.requested_time,
            "status": "response_email_parsed",
            "logs": state.get("logs", []) + [log_entry]
        }
      

def parse_slot(slot_str: str):
    """Parse slot string into (date, start_time, end_time) as datetime objects"""
    # Handle formats like "2026-02-21 from 10:00AM to 11.00 AM"
    pattern = r"(\d{4}-\d{2}-\d{2}) from (\d{1,2}[:.]\d{2}\s*(?:AM|PM)?) to (\d{1,2}[:.]\d{2}\s*(?:AM|PM)?)"
    match = re.search(pattern, slot_str, re.IGNORECASE)
    
    if not match:
        return None
    
    date_str, start_str, end_str = match.groups()

    def normalize_time(t: str) -> str:
        """Normalize time formats: 11.00 AM → 11:00 AM, 12:00 → 12:00 PM"""
        t = t.strip().replace(".", ":")           # 11.00 AM → 11:00 AM
        if not re.search(r"(AM|PM)", t, re.IGNORECASE):
            t += " PM"                            # "12:00" → "12:00 PM"
        return t

    try:
        start_dt = datetime.strptime(f"{date_str} {normalize_time(start_str)}", "%Y-%m-%d %I:%M%p")
        end_dt   = datetime.strptime(f"{date_str} {normalize_time(end_str)}",   "%Y-%m-%d %I:%M%p")
        return start_dt, end_dt, slot_str
    except ValueError:
        return None




def check_availability(state: AgentState) -> dict:
    requested_date = state["requested_date"]   # "2026-02-21"
    requested_time = state["requested_time"]   # "10:00 AM"
    available_slots = list(state["available_slots"])  # copy so we can pop

    # ---- Parse requested datetime ----
    try:
        requested_dt = datetime.strptime(f"{requested_date} {requested_time}", "%Y-%m-%d %I:%M %p")
    except ValueError:
        return {
            "status": "slot_not_found",
            "logs": state["logs"] + ["[check_availability] Could not parse requested date/time"]
        }

    matched_slot = None

    # ---- Search for matching slot ----
    for slot_str in available_slots:
        parsed = parse_slot(slot_str)
        if parsed is None:
            continue
        start_dt, end_dt, original = parsed

        # Check if requested time falls within the slot window
        if start_dt.date() == requested_dt.date() and start_dt <= requested_dt < end_dt:
            matched_slot = original
            available_slots.remove(original)   # ← pop matched slot
            break

    log_entry = f"[check_availability] matched={matched_slot}"

    if matched_slot:
        return {
            "selected_slot": matched_slot,
            "available_slots": available_slots,     # ← updated list without matched slot
            "proposed_slots": [],
            "status": "slot_found",
            "logs": state["logs"] + [log_entry]
        }
    else:
        # Propose 3 slots from same date if possible, else any
        same_date = [s for s in available_slots if requested_date in s]
        proposed = same_date[:] if same_date else available_slots[:]
        print( {
            "selected_slot": None,
            "available_slots": available_slots,
            "proposed_slots": proposed,
            "status": "slot_not_found",
            "logs": state["logs"] + [log_entry]
        })
        return {
            "selected_slot": None,
            "available_slots": available_slots,
            "proposed_slots": proposed,
            "status": "slot_not_found",
            "logs": state["logs"] + [log_entry]
        }


def route_after_availability(state: AgentState) -> Literal["book_appointment", "draft_new_slots_email"]:
    """Conditional edge: route based on slot availability."""
    if state["status"] == "slot_found":
        return "book_appointment"
    return "draft_new_slots_email"

class DraftEmail(BaseModel):
    subject: str
    body: str

def draft_new_slots_email(state: AgentState) -> dict:
    proposed_slots = state["proposed_slots"]
    patient_name   = state["patient_name"]
    patient_email  = state["patient_email"]
    requested_date = state["requested_date"]
    requested_time = state["requested_time"]

    prompt = f"""
    You are a medical scheduling assistant.
    The patient's requested slot was not available. 
    Write a polite email to the patient proposing alternative appointment slots.
    
    Patient Details:
    - Name          : {patient_name}
    - Email         : {patient_email}
    - Requested Date: {requested_date}
    - Requested Time: {requested_time}
    
    Alternative Slots Available:
    {chr(10).join(f"  - {slot}" for slot in proposed_slots)}
    
    The email should:
    - Apologize that the requested slot is unavailable
    - Clearly list the proposed alternative slots
    - Ask the patient to reply with their preferred slot
    - Keep a professional and friendly tone
    """

    structured_llm = llm.with_structured_output(DraftEmail)
    response: DraftEmail = structured_llm.invoke(prompt)

    log_entry = f"[draft_new_slots_email] Draft created for {patient_name} with {len(proposed_slots)} proposed slots"

    return {
        "draft_email"   : response.body,
        "status"        : "draft_ready",
        "logs"          : state["logs"] + [log_entry]
    }

def human_review(state: AgentState) -> AgentState:
    """Skip blocking input() when running from Streamlit."""
    logs = state.get("logs", [])
    
    # ← Streamlit handles approval via UI buttons, so auto-pass here
    logs.append("👤 Human Review: Passed to Streamlit UI for approval")
    return {
        **state,
        "human_approved": False,   # UI will handle this
        "status": "draft_ready",   # Stop here, UI takes over
        "logs": logs,
    }

def send_proposed_slots_email(state: AgentState) -> AgentState:
    """Send the approved email to Patient X."""
    logs = state.get("logs", [])
    logs.append("📤 Sending proposed slots email to Patient X...")
    # send email
    logs.append("   Email sent. Waiting for patient response...")

    return {**state, "status": "waiting_patient_response", "logs": logs}

def receive_patient_response(state: AgentState) -> AgentState:
    patient_info = {
    "name": state["patient_name"],
    "email": state["patient_email"],
    "age": state["patient_age"]}
    PatientXAgent_response = PatientXAgent(
        action="respond_to_slots",
        context=state["draft_email"],
        patient_info=patient_info
    )
    logs = state.get("logs", [])
    
    logs.append(f"📥 Received patient response: {PatientXAgent_response.body}")
    if PatientXAgent_response.accepted:
        status = "patient_accepted"
        logs.append("   Patient accepted a proposed slot.")
    else:
        status = "patient_declined"
        logs.append("   Patient declined the proposed slots.")
    return {
        **state,
        "patient_response": PatientXAgent_response.body,
        "status": status,
        "logs": logs
    }

def route_after_patient_response(state: AgentState):
    """Conditional edge: route based on patient's response to proposed slots."""
    if state["status"] == "patient_accepted":
        return "scan_and_parse_email"  # Loop back to re-parse patient's response email for the accepted slot
    return "end"

def book_appointment(state: AgentState) -> dict:
    confirmed_slot = state["selected_slot"]
    patient_email  = state["patient_email"]
    patient_name   = state["patient_name"]
    patient_age    = state["patient_age"]

    prompt = f"""
    You are a medical scheduling assistant.
    Generate a professional appointment confirmation email from doctorX for the patient.
    
    Patient Details:
    - Name  : {patient_name}
    - Age   : {patient_age}
    - Email : {patient_email}
    
    Confirmed Appointment Slot: {confirmed_slot}
    
    The email should:
    - Confirm the appointment date and time clearly
    - Ask the patient to arrive 10 minutes early
    - Mention to bring any previous medical records
    - Provide a cancellation/rescheduling note
    """

    structured_llm = llm.with_structured_output(ConfirmationEmail)
    response: ConfirmationEmail = structured_llm.invoke(prompt)

    log_entry = f"[appointment_confirmation] Confirmation email generated for {patient_name} at {confirmed_slot}"

    return {
        "confirmation_email": response.body,
        "status": "confirmation_sent",
        "logs": state["logs"] + [log_entry]
    }



# ---- Build the graph ----
graph_builder = StateGraph(AgentState)
graph_builder.add_node("scan_and_parse_email", scan_and_parse_email)
graph_builder.add_node("check_availability", check_availability)
graph_builder.add_node("draft_new_slots_email", draft_new_slots_email)
graph_builder.add_node("human_review", human_review)
graph_builder.add_node("send_proposed_slots_email", send_proposed_slots_email)
graph_builder.add_node("receive_patient_response", receive_patient_response)
graph_builder.add_node("book_appointment",book_appointment)
# graph_builder.add_node("",)

graph_builder.set_entry_point("scan_and_parse_email")
graph_builder.add_edge("scan_and_parse_email", "check_availability")
graph_builder.add_conditional_edges(
        "check_availability",
        route_after_availability,
        {
            "book_appointment": "book_appointment",
            "draft_new_slots_email": "draft_new_slots_email",
        },
    )
graph_builder.add_edge("draft_new_slots_email","human_review")
graph_builder.add_edge("human_review","send_proposed_slots_email")
graph_builder.add_edge("send_proposed_slots_email","receive_patient_response")
# graph_builder.add_edge("receive_patient_response","scan_and_parse_email")  # Loop back to re-parse patient's response email
graph_builder.add_conditional_edges(
        "receive_patient_response",
        route_after_patient_response,
        {
            "scan_and_parse_email": "scan_and_parse_email",
            "end": END
        },
    )
graph_builder.add_edge("book_appointment",END)

graph = graph_builder.compile()

# available_slots: 

initial_state = {
    "raw_email": "",
    "patient_name": "",
    "patient_age": None,
    "patient_email": "",
    "requested_date": None,
    "requested_time": None,
    "available_slots": [
    "2026-02-21 from 9:00AM to 10:00AM",
    "2026-02-21 from 10:00AM to 11:00AM",
    "2026-02-21 from 11:00AM to 12:00PM",
    "2026-02-21 from 1:00PM to 2:00PM",
    "2026-02-21 from 2:00PM to 3:00PM",   # ← was 2:00AM
    "2026-02-21 from 3:00PM to 4:00PM",   # ← was 3:00AM
    "2026-02-22 from 10:00AM to 11:00AM",
    "2026-02-22 from 1:00PM to 2:00PM",
    "2026-02-22 from 2:00PM to 3:00PM",   # ← was 2:00AM
    "2026-02-22 from 3:00PM to 4:00PM",   # ← was 3:00AM
    ],
    "selected_slot": None,
    "human_approved": False,
    "human_feedback": None,
    "patient_response": None,
    "draft_email": None,
    "proposed_slots": [],
    "status": "started",
    "iteration": 0,
    "logs": []
}
# while True:
#     i = input("Enter 0 to stop, any other number to continue: ")
#     if i == "0":
#         break

#     # ---- Generate a fresh patient email each iteration ----
#     patient_response = PatientXAgent(action="write_email")
#     print(f"\n📧 Patient Email:\n{patient_response.body}\n")

#     initial_state["raw_email"] = patient_response.body  # ← update each time

#     result = graph.invoke(initial_state)

#     # ---- Update available slots for next iteration ----
#     initial_state["available_slots"] = result.get("available_slots", initial_state["available_slots"])

#     print("✅ Result:")
#     print(f"  Name            : {result['patient_name']}")
#     print(f"  Age             : {result['patient_age']}")
#     print(f"  Email           : {result['patient_email']}")
#     print(f"  Date            : {result['requested_date']}")
#     print(f"  Time            : {result['requested_time']}")
#     print(f"  Status          : {result['status']}")
#     print(f"  Selected Slot   : {result['selected_slot']}")
#     print(f"  Proposed Slots  : {result['proposed_slots']}")
#     print(f"  Draft Email     : {result['draft_email']}")
#     print(f"  Available Slots : {result['available_slots']}")
#     print(f"  Logs            : {result['logs']}")
#     print("-" * 60)



# agent.py (add at the bottom)

def run_agent(raw_email: str, available_slots: list) -> dict:
    """Single entry point for the Streamlit UI to call."""
    initial_state = {
        "raw_email": raw_email,
        "patient_name": "",
        "patient_age": None,
        "patient_email": "",
        "requested_date": None,
        "requested_time": None,
        "available_slots": available_slots,
        "selected_slot": None,
        "human_approved": False,
        "human_feedback": None,
        "patient_response": None,
        "draft_email": None,
        "confirmation_email": None,
        "proposed_slots": [],
        "status": "started",
        "iteration": 0,
        "logs": []
    }
    result = graph.invoke(initial_state)
    return result


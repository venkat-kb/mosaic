import speech_recognition as sr
from datetime import datetime
import uuid
import json

from .models import CaseRecord
from .input import extract_incident_details
from .spamfilteringactual import HelplineProcessor
from .simitestllm import subredditting
from .scoring import scoring

from db.supabase import create_supabase_client  

def process_call_transcript(transcript: str, caller_phone: str):
    print(f"Processing transcript for {caller_phone}: '{transcript}'")

    try:
        details_json = extract_incident_details(transcript)
        details = json.loads(details_json)

        if "error" in details or not details.get("case_detail"):
            print("Could not extract valid grievance details from transcript.")
            return

        case_id = str(uuid.uuid4())
        grievance = CaseRecord(
            case_no=case_id,
            date=datetime.now(),
            detail=details.get("case_detail"),
            location=details.get("location", "Unknown"),
            caller=details.get("caller_name", "Unknown"),
            phone_no=caller_phone,
            status="PENDING",
            sub_reddit_id=case_id  # Initially, it's its own thread
        )

        processor = HelplineProcessor()
        result = processor.process_grievance_object(grievance)

        # If not spam, continue with the rest of your pipeline
        if result:
            print("Grievance is NOT spam. Proceeding to save and score.")
            supabase = create_supabase_client()
            # Convert dataclass to dict for Supabase and handle datetime
            grievance_dict = result.__dict__
            grievance_dict['date'] = grievance_dict['date'].isoformat()
            supabase.table("Complaint").insert(grievance_dict).execute()

            # Pass the CaseRecord object to the next steps
            subredditting(result)
            scoring()
            print("Grievance processing complete.")
        else:
            print("Grievance flagged as SPAM. Processing stopped.")

    except Exception as e:
        print(f"An unexpected error occurred during transcript processing: {e}")

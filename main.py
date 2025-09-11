from pydantic import BaseModel
from components.models import CaseRecord
from components.gui import gui

from components.spamfilteringactual import HelplineProcessor
from components.simitestllm import subredditting
from components.scoring import scoring
from datetime import datetime




# def main():
#     grievance = Grievance(
#         caller_name="Advita",
#         caller_phone_no="9582707021",
#         location="Mathura",
#         description="There are insects infesting my house, please help",
#         date_time="2025-06-10 16:14:40",
#     )
    # processor = HelplineProcessor()
    # result = processor.process_grievance_object(grievance)
    # if result:
    #     subredditting(result)
    #     scoring()


# if __name__ == "__main__":
#     main()

from typing import Union

from fastapi import FastAPI, Body

from db.supabase import create_supabase_client

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}

class ComplaintRequest(BaseModel):
    details: str
    location: str
    caller: str
    phone: str

supabase = create_supabase_client()

@app.post("/api/v1/new-complaint")
async def new_complaint(complaint: ComplaintRequest = Body(...)):
    # Get the current date and time
    print("f ts fr")
    current_datetime = datetime.now()
    grievance = CaseRecord(
        case_no = None,
        case_category = None,
        date=current_datetime,
        detail=complaint.details,
        location=complaint.location,
        priority= None,
        score= None,  
        status="OPEN",   
        caller=complaint.caller,
        phone_no=complaint.phone,
        sub_reddit_id= None)
    processor = HelplineProcessor()
    print("P", processor)
    result = processor.process_grievance_object(grievance)
    print("r", result)
    if result:
        print("f ts frfr")
        subredditting(result)
        scoring()

    return {
        "details": complaint.details, 
        "location": complaint.location, 
        "caller": complaint.caller, 
        "phone": complaint.phone
    }

@app.get("/complaints")
async def get_complaints():
    """Fetch all complaints from the database."""
    data = supabase.table("Complaint").select("*").execute()
    return data.data if data else []
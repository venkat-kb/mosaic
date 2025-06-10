from datetime import datetime
from typing import List, Dict
from dataclasses import dataclass, field


@dataclass
class Grievance:
    caller_name: str
    caller_phone_no: str
    description: str
    location: str
    date_time: datetime


@dataclass
class CaseRecord:
    case_no: str
    case_category: str
    case_detail: str
    problem_start: str  # or datetime
    location: str
    priority: int
    score: int  # specify types if needed e.g., Dict[str, int]
    thread: List[Grievance] = field(default_factory=list)


class Category:
    name: str
    priority: int


# case = CaseRecord(
#     case_no="asdfgh",
#     case_category="",
#     case_detail="Power outage",
#     problem_start="date of last night",
#     location="Lucknow, UP",
#     urgency=0,
#     scoring={},
#     thread=[
#         Grievance(
#             caller_name="Diff name",
#             caller_phone_no=9876543210,
#             description="My building has no power",
#             location="Lucknow",
#             date_time="2025-06-09 12:00",
#         )
#     ],
# )

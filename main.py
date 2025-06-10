from components.input import GrievanceAgent
from components.models import CaseRecord, Grievance
from components.scoring import classify_case_priority_flexible
from components.spam_filtering import HelplineProcessor


def main():
    try:
        # agent = GrievanceAgent()
        # grievance = agent.run_conversation()

        # print(grievance)

        grievance = Grievance(
            caller_name="Aryan",
            caller_phone_no="9582707063",
            location="Noida",
            description="I have no water in my house",
            date_time="2025-06-10 16:14:40",
        )

        processor = HelplineProcessor()
        result = processor.process_grievance_object(grievance)

        if result:
            print(result)
            # Thread mapping

            # Scoring
            case = CaseRecord(
                {
                    "case_no": "CASE-001",
                    "case_category": {
                        "name": "Energy, Power & Electricity",
                        "semantic_weight": 5.4,
                        "keywords": [
                            "power generation",
                            "electricity",
                            "renewable energy",
                            "energy efficiency",
                            "energy policy",
                            "solar power",
                            "wind energy",
                            "energy infrastructure",
                            "energy conservation",
                            "energy audits",
                            "energy grants",
                            "energy technology",
                            "energy sustainability",
                            "energy research",
                            "energy exports",
                            "energy education",
                            "energy equipment",
                            "energy standards",
                            "energy monitoring",
                            "energy accountability",
                            "energy reforms",
                            "energy outreach",
                            "energy awareness",
                            "energy impact",
                            "energy governance",
                            "energy partnerships",
                            "energy services",
                            "energy equity",
                            "energy planning",
                            "energy modernization",
                        ],
                    },
                    "case_detail": "No water supply for 3 days",
                    "problem_start": "2023-06-10 08:00:00",
                    "location": "Lucknow",
                    "priority": "medium",
                    "score": 1.2576815101390457,
                    "status": "open",
                    "thread": [
                        {
                            "caller_name": "Aarav Sharma",
                            "caller_phone_no": "9876543210",
                            "description": "No water in Gomti Nagar since Monday",
                            "location": "Lucknow",
                            "date_time": "2023-06-10T09:23:45",
                        },
                        {
                            "caller_name": "Priya Singh",
                            "caller_phone_no": "9567843210",
                            "description": "Water supply not restored in sector 5",
                            "location": "Lucknow",
                            "date_time": "2023-06-10T11:45:30",
                        },
                    ],
                },
            )

            alpha = 0.5
            classify_case_priority_flexible(case, alpha)

            # Deparment go go

            # Feedback loop

    except KeyboardInterrupt:
        print("\n[SYSTEM] Conversation ended by user. Goodbye.")
    except Exception as e:
        print(f"\n[FATAL ERROR] An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()

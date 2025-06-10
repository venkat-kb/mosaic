from components.input import GrievanceAgent
from components.models import CaseRecord, Grievance

# from components.scoring import classify_case_priority_flexible
from components.spam_filtering import HelplineProcessor
from subreddit.simitestllm import subredditting
from components.scoring import scoring


def main():
    try:
        # agent = GrievanceAgent()
        # grievance = agent.run_conversation()

        # print(grievance)

        grievance = Grievance(
            caller_name="Aryan",
            caller_phone_no="9582707063",
            location="Noida",
            description="My house is burning down",
            date_time="2025-06-10 16:14:40",
        )

        processor = HelplineProcessor()
        result = processor.process_grievance_object(grievance)

        if result:
            print(result)
            # Thread mapping
            subredditting(result)

            # Scoring
            scoring()

            # Deparment go go

            # Feedback loop

    except KeyboardInterrupt:
        print("\n[SYSTEM] Conversation ended by user. Goodbye.")
    except Exception as e:
        print(f"\n[FATAL ERROR] An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()

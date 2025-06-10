from components.input import GrievanceAgent
from components.models import Grievance
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

            # Deparment go go

            # Feedback loop

    except KeyboardInterrupt:
        print("\n[SYSTEM] Conversation ended by user. Goodbye.")
    except Exception as e:
        print(f"\n[FATAL ERROR] An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()

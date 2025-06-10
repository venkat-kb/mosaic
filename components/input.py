import speech_recognition as sr
from datetime import datetime
import json
import google.generativeai as genai
import pyttsx3
import os

from .models import Grievance
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


def extract_incident_details(text):
    """
    Extracts caller name, phone number, location, case detail, and date/time of incident
    from a given string using the Gemini API. It identifies missing information and
    formulates questions to ask, returning the entire object as a JSON string.

    Args:
        text (str): The input string containing incident details.

    Returns:
        str: A JSON string containing the extracted details and questions,
             or an error message if the API call fails or parsing issues occur.
    """
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")

        prompt = f"""
        Analyze the following incident report text, which may be a transcript of a conversation.
        Extract the key information. The conversation might include explicit questions and answers.
        Return the information as a JSON object with the following keys:
        - "caller_name": (string) The name of the person reporting the incident. If not found, use null.
        - "phone_number": (string) The contact phone number. If not found, use null.
        - "location": (string) The location mentioned where the incident occurred. If not found, use null.
        - "case_detail": (string) A brief description of the incident or problem. If not found, use null.
        - "incident_datetime": (string) The date and/or time of the incident, if mentioned. If not found, use null.
        - "questions": (array of strings) A list of questions to ask to gather any missing information from the above fields. The list should be empty if all information is present.

        Incident Report Text:
        "{text}"
        """

        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                response_mime_type="application/json"
            ),
        )

        parsed_data = json.loads(response.text)
        parsed_data["report_datetime"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return json.dumps(parsed_data, indent=4)

    except Exception as e:
        print(f"[ERROR] Gemini API call failed: {e}")
        return json.dumps(
            {"error": f"An error occurred with the API: {e}", "original_text": text},
            indent=4,
        )


class GrievanceAgent:
    def __init__(self, pause_threshold=1.0):
        """
        Initializes the conversational grievance agent.
        """
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()

        self.tts_engine = pyttsx3.init()

        self.grievance_transcript = ""

        print("Calibrating microphone... Please be quiet for a moment.")
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
        print("Microphone calibrated.")

        self.recognizer.pause_threshold = pause_threshold

    def speak(self, text):
        """
        Converts text to speech.
        """
        print(f"\n[AGENT]: {text}")
        self.tts_engine.say(text)
        self.tts_engine.runAndWait()

    def listen_for_speech(self, timeout=10):
        """
        Listens for a single utterance from the user and returns the text.
        """
        with self.microphone as source:
            print("[LISTENING...]")
            try:
                audio = self.recognizer.listen(
                    source, timeout=timeout, phrase_time_limit=15
                )
                text = self.recognizer.recognize_google(audio)
                print(f"[USER]: {text}")
                return text
            except sr.WaitTimeoutError:
                self.speak("I didn't hear anything. Let's try again.")
                return None
            except sr.UnknownValueError:
                self.speak(
                    "I'm sorry, I could not understand what you said. Please repeat."
                )
                return None
            except sr.RequestError as e:
                self.speak(
                    "There seems to be a service error. Please check your connection."
                )
                print(f"Speech recognition service error: {e}")
                return None

    def run_conversation(self):
        """
        Manages the entire conversation flow.
        """
        self.speak("1071, how can I help you?")

        initial_grievance = self.listen_for_speech()
        if not initial_grievance:
            self.speak(
                "It seems we got disconnected. Please try calling again. Goodbye."
            )
            return

        self.grievance_transcript = f"Initial statement: {initial_grievance}"

        while True:
            print("\n-------------------------------------------")
            print("[SYSTEM] Processing transcript with Gemini...")

            response_json = extract_incident_details(self.grievance_transcript)

            try:
                data = json.loads(response_json)
            except json.JSONDecodeError:
                self.speak(
                    "I encountered a system error while processing your request. Please try again."
                )
                print(f"[ERROR] Failed to parse JSON: {response_json}")
                break

            if "error" in data:
                self.speak(
                    "I'm having trouble connecting to my system. Please try again later."
                )
                break

            questions = data.get("questions", [])

            if not questions:
                self.speak(
                    "Thank you. I have all the information I need. Your report has been filed."
                )
                print("\n--- FINAL REPORT ---")
                print(response_json)
                data = json.loads(response_json)
                return Grievance(
                    caller_name=data.get("caller_name"),
                    caller_phone_no=data.get("phone_number"),
                    description=data.get("case_detail"),
                    location=data.get("location"),
                    date_time=data.get("report_datetime"),
                )

            question_to_ask = questions[0]
            self.speak(question_to_ask)

            answer = self.listen_for_speech()

            if answer:
                self.grievance_transcript += (
                    f"\nAgent Question: {question_to_ask}\nUser Answer: {answer}"
                )
            else:
                self.speak(
                    "I didn't catch an answer. Let me re-process and we can try again."
                )


# def main():
#     """Main function to run the grievance agent."""
#     try:
#         agent = GrievanceAgent()
#         grievance = agent.run_conversation()

#     except KeyboardInterrupt:
#         print("\n[SYSTEM] Conversation ended by user. Goodbye.")
#     except Exception as e:
#         print(f"\n[FATAL ERROR] An unexpected error occurred: {e}")


# if __name__ == "__main__":
#     main()

import speech_recognition as sr
from datetime import datetime
import json
import google.generativeai as genai
import pyttsx3
import os
from dotenv import load_dotenv

# Define the Grievance model class
class Grievance:
    def __init__(self, caller_name=None, caller_phone_no=None, description=None, location=None, date_time=None):
        self.caller_name = caller_name
        self.caller_phone_no = caller_phone_no
        self.description = description
        self.location = location
        self.date_time = date_time
    
    def to_dict(self):
        return {
            "caller_name": self.caller_name,
            "caller_phone_no": self.caller_phone_no,
            "description": self.description,
            "location": self.location,
            "date_time": self.date_time
        }

load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Supported Indian languages mapping
INDIAN_LANGUAGES = {
    'hindi': 'hi',
    'bengali': 'bn', 
    'telugu': 'te',
    'marathi': 'mr',
    'tamil': 'ta',
    'gujarati': 'gu',
    'urdu': 'ur',
    'kannada': 'kn',
    'odia': 'or',
    'punjabi': 'pa',
    'malayalam': 'ml',
    'assamese': 'as',
    'maithili': 'mai',
    'santali': 'sat',
    'kashmiri': 'ks'
}

class GeminiLanguageWrapper:
    """
    A wrapper class for Gemini 2.5 Pro API to handle language translation and processing
    """
    
    def __init__(self):
        self.model = genai.GenerativeModel("gemini-1.5-flash")
    
    def detect_language(self, text):
        """
        Detect the language of the input text using Gemini API
        
        Args:
            text (str): Input text to detect language
            
        Returns:
            str: Detected language code or 'en' for English
        """
        try:
            prompt = f"""
            Detect the language of the following text. Return only the language name in lowercase.
            If it's one of these Indian languages, return the exact name: {', '.join(INDIAN_LANGUAGES.keys())}.
            If it's English, return 'english'.
            If uncertain, return 'english'.
            
            Text: "{text}"
            """
            
            response = self.model.generate_content(prompt)
            detected_lang = response.text.strip().lower()
            
            # Return language code or 'en' for English
            if detected_lang == 'english':
                return 'en'
            elif detected_lang in INDIAN_LANGUAGES:
                return INDIAN_LANGUAGES[detected_lang]
            else:
                return 'en'  # Default to English
                
        except Exception as e:
            print(f"[ERROR] Language detection failed: {e}")
            return 'en'  # Default to English on error
    
    def translate_to_english(self, text, source_language=None):
        """
        Translate text from Indian language to English using Gemini API
        
        Args:
            text (str): Text to translate
            source_language (str): Source language code (optional)
            
        Returns:
            str: Translated English text
        """
        try:
            if source_language and source_language == 'en':
                return text  # Already in English
            
            prompt = f"""
            Translate the following text to English. If the text is already in English, return it as is.
            Maintain the meaning and context of the original text, especially for grievance or complaint scenarios.
            
            Text: "{text}"
            
            Return only the English translation without any additional explanation.
            """
            
            response = self.model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            print(f"[ERROR] Translation failed: {e}")
            return text  # Return original text on error
    
    def translate_from_english(self, text, target_language):
        """
        Translate text from English to target Indian language using Gemini API
        
        Args:
            text (str): English text to translate
            target_language (str): Target language code
            
        Returns:
            str: Translated text in target language
        """
        try:
            if target_language == 'en':
                return text  # Already in English
            
            # Find language name from code
            target_lang_name = None
            for lang_name, lang_code in INDIAN_LANGUAGES.items():
                if lang_code == target_language:
                    target_lang_name = lang_name
                    break
            
            if not target_lang_name:
                return text  # Return original if language not found
            
            prompt = f"""
            Translate the following English text to {target_lang_name}.
            Maintain the formal and respectful tone appropriate for official communication.
            
            English text: "{text}"
            
            Return only the {target_lang_name} translation without any additional explanation.
            """
            
            response = self.model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            print(f"[ERROR] Translation to {target_language} failed: {e}")
            return text  # Return original text on error


def extract_incident_details(text):
    """
    Extracts caller name, phone number, location, case detail, and date/time of incident
    from a given string using the Gemini 2.5 Pro API. It identifies missing information and
    formulates questions to ask, returning the entire object as a JSON string.

    Args:
        text (str): The input string containing incident details (in English).

    Returns:
        str: A JSON string containing the extracted details and questions,
             or an error message if the API call fails or parsing issues occur.
    """
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")

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
        Initializes the conversational grievance agent with multi-language support.
        """
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.tts_engine = pyttsx3.init()
        self.grievance_transcript = ""
        self.language_wrapper = GeminiLanguageWrapper()
        self.user_language = 'en'  # Default to English
        
        print("Calibrating microphone... Please be quiet for a moment.")
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
        print("Microphone calibrated.")

        self.recognizer.pause_threshold = pause_threshold

    def speak(self, text):
        """
        Converts text to speech, translating to user's language if needed.
        """
        # Translate to user's language if not English
        if self.user_language != 'en':
            translated_text = self.language_wrapper.translate_from_english(text, self.user_language)
            print(f"\n[AGENT - {self.user_language}]: {translated_text}")
            print(f"[AGENT - English]: {text}")
        else:
            translated_text = text
            print(f"\n[AGENT]: {text}")
        
        # Use English for TTS (can be enhanced to support Indian language TTS)
        self.tts_engine.say(text)
        self.tts_engine.runAndWait()

    def listen_for_speech(self, timeout=10):
        """
        Listens for a single utterance from the user, detects language, and translates to English.
        """
        with self.microphone as source:
            print("[LISTENING...]")
            try:
                audio = self.recognizer.listen(
                    source, timeout=timeout, phrase_time_limit=15
                )
                # Try Hindi first for Indian users, then fallback to English
                try:
                    text = self.recognizer.recognize_google(audio, language='hi-IN')
                    detected_lang = self.language_wrapper.detect_language(text)
                    if detected_lang != 'en':
                        self.user_language = detected_lang
                        print(f"[USER - {detected_lang}]: {text}")
                        # Translate to English for processing
                        english_text = self.language_wrapper.translate_to_english(text, detected_lang)
                        print(f"[USER - English]: {english_text}")
                        return english_text
                    else:
                        print(f"[USER]: {text}")
                        return text
                except sr.UnknownValueError:
                    # Fallback to English if Hindi recognition fails
                    text = self.recognizer.recognize_google(audio, language='en-IN')
                    print(f"[USER]: {text}")
                    self.user_language = 'en'
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


def main():
    """Main function to run the grievance agent."""
    try:
        print("=== Multi-Language Grievance System ===")
        print("Supported Languages:")
        for lang_name, lang_code in INDIAN_LANGUAGES.items():
            print(f"  - {lang_name.title()} ({lang_code})")
        print("  - English (en)")
        print("\nStarting grievance agent...")
        
        agent = GrievanceAgent()
        grievance = agent.run_conversation()
        
        if grievance:
            print("\n=== FINAL GRIEVANCE REPORT ===")
            print(json.dumps(grievance.to_dict(), indent=4))

    except KeyboardInterrupt:
        print("\n[SYSTEM] Conversation ended by user. Goodbye.")
    except Exception as e:
        print(f"\n[FATAL ERROR] An unexpected error occurred: {e}")


def test_translation():
    """Test function to verify translation capabilities."""
    print("=== Testing Translation Functionality ===")
    
    # Create language wrapper
    wrapper = GeminiLanguageWrapper()
    
    # Test phrases in different languages
    test_phrases = [
        ("नमस्ते, मुझे शिकायत करनी है", "Hindi"),
        ("আমার একটি অভিযোগ আছে", "Bengali"), 
        ("मला तक्रार करायची आहे", "Marathi"),
        ("എനിക്ക് ഒരു പരാതിയുണ്ട്", "Malayalam"),
        ("I have a complaint to make", "English")
    ]
    
    print("\nTesting language detection and translation:")
    for phrase, expected_lang in test_phrases:
        print(f"\nOriginal: {phrase} ({expected_lang})")
        
        # Detect language
        detected = wrapper.detect_language(phrase)
        print(f"Detected language: {detected}")
        
        # Translate to English
        english_translation = wrapper.translate_to_english(phrase, detected)
        print(f"English translation: {english_translation}")
        
        # Translate back if not English
        if detected != 'en':
            back_translation = wrapper.translate_from_english(english_translation, detected)
            print(f"Back translation: {back_translation}")


def test_grievance_processing():
    """Test function to verify grievance processing without speech."""
    print("=== Testing Grievance Processing ===")
    
    # Test sample grievances in different languages
    test_grievances = [
        "मेरा नाम राहुल है। मेरा फोन नंबर 9876543210 है। मुझे दिल्ली में बिजली की समस्या की शिकायत करनी है।",
        "আমার নাম অমিত। আমার ফোন নম্বর ৯৮৭৬৫৪৩২১০। কলকাতায় পানির সমস্যা নিয়ে অভিযোগ করতে চাই।",
        "My name is John. My phone number is 9876543210. I want to report a road problem in Mumbai."
    ]
    
    wrapper = GeminiLanguageWrapper()
    
    for i, grievance in enumerate(test_grievances, 1):
        print(f"\n--- Test Case {i} ---")
        print(f"Original: {grievance}")
        
        # Detect and translate
        detected_lang = wrapper.detect_language(grievance)
        english_grievance = wrapper.translate_to_english(grievance, detected_lang)
        print(f"English: {english_grievance}")
        
        # Process with incident details extraction
        result = extract_incident_details(english_grievance)
        print(f"Extracted details: {result}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--test-translation":
            test_translation()
        elif sys.argv[1] == "--test-processing":
            test_grievance_processing()
        elif sys.argv[1] == "--test-all":
            test_translation()
            print("\n" + "="*50 + "\n")
            test_grievance_processing()
        else:
            print("Usage:")
            print("  python input.py                    # Run the full grievance system")
            print("  python input.py --test-translation # Test translation functionality")
            print("  python input.py --test-processing  # Test grievance processing")
            print("  python input.py --test-all         # Run all tests")
    else:
        main()

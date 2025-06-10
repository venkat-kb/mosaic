import json
import re
import datetime
from typing import Dict, List, Tuple, Optional
from collections import defaultdict

from models import Grievance

try:
    from langdetect import detect

    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False

try:
    import spacy

    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False

try:
    from transformers import pipeline

    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

try:
    import dateparser

    DATEPARSER_AVAILABLE = True
except ImportError:
    DATEPARSER_AVAILABLE = False


class HelplineProcessor:
    """Main class for processing helpline transcriptions."""

    def __init__(self):
        """Initialize the processor with required models and data."""
        self.nlp_en = None
        self.ner_pipeline = None
        self.spam_tracker = defaultdict(list)  # Track repeated submissions
        self.load_models()
        self.setup_data()

    def load_models(self):
        """Load NLP models and pipelines."""
        try:
            # Load spaCy models if available
            if SPACY_AVAILABLE:
                try:
                    self.nlp_en = spacy.load("en_core_web_lg")
                except OSError:
                    print(
                        "English spaCy model not found. Install with: python -m spacy download en_core_web_lg"
                    )

            # Load transformers NER pipeline if available
            if TRANSFORMERS_AVAILABLE:
                try:
                    self.ner_pipeline = pipeline(
                        "ner",
                        model="dbmdz/bert-large-cased-finetuned-conll03-english",
                        aggregation_strategy="simple",
                    )
                except Exception:
                    print(
                        "Could not load transformers NER pipeline. Using spaCy instead."
                    )

        except Exception as e:
            print(f"Warning: Could not load all models: {e}")

    def setup_data(self):
        """Setup reference data for location validation and spam detection."""
        # UP PIN code ranges
        self.up_pin_ranges = [
            (200000, 299999),  # UP PIN codes
        ]

        # Common UP cities and areas
        self.up_locations = {
            "lucknow",
            "kanpur",
            "agra",
            "varanasi",
            "meerut",
            "allahabad",
            "prayagraj",
            "bareilly",
            "ghaziabad",
            "noida",
            "aligarh",
            "gorakhpur",
            "saharanpur",
            "muzaffarnagar",
            "mathura",
            "firozabad",
            "jhansi",
            "unnao",
            "sitapur",
            "etawah",
            "orai",
            "hardoi",
            "fatehpur",
            "ayodhya",
            "faizabad",
            "sultanpur",
            "azamgarh",
            "bulandshahr",
            "hapur",
            "sambhal",
            "amroha",
            "rampur",
            "moradabad",
            "shahjahanpur",
            "farrukhabad",
            "etah",
            "mainpuri",
            "budaun",
            "bareilly",
            "pilibhit",
            "lakhimpur",
            "sitapur",
            "kheri",
        }

        # Grievance keywords
        self.grievance_keywords = {
            "english": [
                "problem",
                "issue",
                "complaint",
                "grievance",
                "trouble",
                "difficulty",
                "water",
                "electricity",
                "road",
                "pothole",
                "drainage",
                "sewage",
                "garbage",
                "street light",
                "corruption",
                "bribery",
                "harassment",
                "police",
                "hospital",
                "school",
                "transport",
                "bus",
                "broken",
                "damaged",
            ]
        }

        # Common spam indicators
        self.spam_indicators = [
            "test",
            "testing",
            "check",
            "hello",
            "hi",
            "namaste",
            "just checking",
            "time pass",
            "मजाक",
            "टेस्ट",
        ]

    def extract_name(self, text: str, language: str) -> Optional[str]:
        """Extract caller's name from the text. Improved: stop at punctuation, keywords, or numbers."""
        name_patterns = [
            r"(?:my name is|i am|i\'m|this is|name:|naam:)[\s,]+([A-Za-z .]{2,60})",
            r"(?:this is|speaking|calling)[\s,]+([A-Za-z .]{2,60})",
        ]
        for pattern in name_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                name = match.group(1)
                # Stop at punctuation, keywords, or numbers
                name = re.split(
                    r"[.,;\d]|\b(from|in|at|of|se|pin|contact|phone|number|area|city|district|village|sector|block|ward|and|but|or|calling|speaking|am|is|are|was|were|have|has|had|will|shall|can|may|should|would|could|might|must|do|does|did|to|for|with|by|on|as|if|that|than|then|when|while|where|who|whom|whose|which|what|how|why)\b",
                    name,
                )[0]
                name = re.sub(r"[^A-Za-z .]", "", name).strip()
                name = re.sub(r"\s+", " ", name).strip(". ")
                # Avoid extracting city names as names
                if (
                    name
                    and name.lower() not in self.up_locations
                    and len(name.split()) >= 1
                ):
                    return name
        # Fallback: try to extract after 'I am' or 'Name:'
        fallback = re.search(
            r"(?:i am|name:)[\s,]*([A-Za-z]{2,20})", text, re.IGNORECASE
        )
        if fallback:
            name = fallback.group(1)
            if name and name.lower() not in self.up_locations:
                return name
        return None

    def extract_phone_number(self, text: str) -> Optional[str]:
        """Extract phone number from the text."""
        # Indian phone number patterns
        phone_patterns = [
            r"(?:\+91|91)?\s*[6-9]\d{9}",  # Indian mobile numbers
            r"(?:phone|number|contact|mob|mobile)[\s:]*(?:\+91|91)?\s*([6-9]\d{9})",
            r"([6-9]\d{9})",  # Simple 10-digit number
        ]

        for pattern in phone_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                # Clean and validate
                number = re.sub(r"\D", "", str(match))
                if len(number) == 10 and number[0] in "6789":
                    return number
                elif len(number) == 12 and number.startswith("91"):
                    return number[2:]

        return None

    def extract_location(self, text: str, language: str) -> Optional[str]:
        """Extract location information from the text. Improved: extract city and PIN, avoid extracting names as locations."""
        # Look for patterns like 'from <city>[, PIN <pincode>]' or 'in <area/city>'
        city_pin_pattern = r"from\s+([A-Za-z ]+)(?:,?\s*PIN\s*(\d{6}))?"
        match = re.search(city_pin_pattern, text, re.IGNORECASE)
        if match:
            city = match.group(1).strip()
            pin = match.group(2)
            if city.lower() in self.up_locations or city:
                if pin:
                    return f"{city.title()}, PIN {pin}"
                else:
                    return city.title()
        # Fallback: PIN code only
        pin_match = re.search(r"\b(2\d{5})\b", text)
        if pin_match:
            pin_code = pin_match.group(1)
            return f"PIN {pin_code}"
        # Fallback: city/area after 'in', 'at', 'area', etc.
        loc_pattern = r"(?:in|at|area|city|district|village|sector|block|ward)\s+([A-Za-z ]{3,40})"
        match = re.search(loc_pattern, text, re.IGNORECASE)
        if match:
            loc = match.group(1).strip()
            if loc.lower() not in self.up_locations and loc.lower() not in text.lower():
                return loc.title()
        # Fallback: known UP locations in text
        for up_loc in self.up_locations:
            if up_loc in text.lower():
                return up_loc.title()
        return None

    def extract_grievance(self, text: str, language: str) -> Optional[str]:
        """Extract the main grievance description."""
        # Look for sentences containing grievance keywords
        grievance_keywords = self.grievance_keywords.get(
            language, self.grievance_keywords["english"]
        )

        sentences = re.split(r"[.!?।]", text)

        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 10:  # Minimum length
                for keyword in grievance_keywords:
                    if keyword.lower() in sentence.lower():
                        # Clean up the sentence
                        grievance = re.sub(r"^[^\w]*", "", sentence)
                        grievance = re.sub(r"[^\w]*$", "", grievance)
                        if len(grievance) > 15:  # Ensure meaningful content
                            return grievance[:200]  # Limit length

        # Fallback: return the longest sentence if no keywords found
        if sentences:
            longest = max(sentences, key=len).strip()
            if len(longest) > 15:
                return longest[:200]

        return None

    def extract_time(self, text: str, language: str) -> Optional[str]:
        """Extract time when the issue started. Output as DD-MM-YY. Handle more variants."""
        now = datetime.datetime.now()
        patterns = [
            (r"for the past (\d+) days?", "days"),
            (r"for past (\d+) days?", "days"),
            (r"for (\d+) days?", "days"),
            (r"since the last (\d+) days?", "days"),
            (r"since last (\d+) days?", "days"),
            (r"for (\d+) weeks?", "weeks"),
            (r"for (\d+) months?", "months"),
            (r"since (yesterday)", "yesterday"),
            (r"since (today)", "today"),
            (r"since last week", "week"),
            (r"Time[:\s-]*(\d+)[-\s]*days?", "days"),
            (r"(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})", "date"),
            (r"happened (\d+) days? ago", "days"),
            (r"happened yesterday", "yesterday"),
        ]
        for pattern, typ in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if typ == "days":
                    days = int(match.group(1))
                    target = now - datetime.timedelta(days=days)
                    return target.strftime("%d-%m-%y")
                elif typ == "weeks":
                    weeks = int(match.group(1))
                    target = now - datetime.timedelta(weeks=weeks)
                    return target.strftime("%d-%m-%y")
                elif typ == "months":
                    months = int(match.group(1))
                    target = now - datetime.timedelta(days=30 * months)
                    return target.strftime("%d-%m-%y")
                elif typ == "yesterday":
                    target = now - datetime.timedelta(days=1)
                    return target.strftime("%d-%m-%y")
                elif typ == "today":
                    return now.strftime("%d-%m-%y")
                elif typ == "week":
                    target = now - datetime.timedelta(weeks=1)
                    return target.strftime("%d-%m-%y")
                elif typ == "date":
                    try:
                        import dateparser

                        parsed = dateparser.parse(match.group(1))
                        if parsed:
                            return parsed.strftime("%d-%m-%y")
                    except Exception:
                        pass
        return ""

    def detect_spam(
        self, text: str, phone_number: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """Detect if the message is spam with improved logic."""
        text_lower = text.lower()

        # Check for spam indicators - but be more contextual
        spam_trigger_count = 0
        for indicator in self.spam_indicators:
            if indicator in text_lower:
                # If it's just a greeting but has real content, don't flag as spam
                if indicator in ["hello", "hi", "namaste"] and len(text.split()) > 8:
                    # Check if there's substantial content after the greeting
                    continue
                elif (
                    indicator in ["test", "testing", "check"] and len(text.split()) < 6
                ):
                    # Only flag short test messages
                    spam_trigger_count += 1
                elif indicator in ["मजाक", "टेस्ट", "time pass"]:
                    spam_trigger_count += 1

        if spam_trigger_count > 0 and len(text.split()) < 10:
            return True, "Non-grievance content"

        # Check for repeated phrases - FIXED: Better detection logic
        words = text_lower.split()
        if len(words) > 3:
            # Count consecutive repeated words or phrases
            repeated_sequences = 0
            for i in range(len(words) - 1):
                if words[i] == words[i + 1] and len(words[i]) > 2:
                    repeated_sequences += 1

            # Check for repeated patterns
            word_freq = {}
            for word in words:
                if len(word) > 2:  # Only consider meaningful words
                    word_freq[word] = word_freq.get(word, 0) + 1

            # If any word appears more than 40% of the time, it's likely spam
            max_freq = max(word_freq.values()) if word_freq else 0
            if max_freq > len(words) * 0.4 or repeated_sequences >= 3:
                return True, "Repeated phrases"

        # Check grievance keywords - be more lenient for Hindi
        all_keywords = self.grievance_keywords["english"]
        has_grievance_keyword = any(
            keyword.lower() in text_lower for keyword in all_keywords
        )

        # Additional meaningful content check
        meaningful_words = [
            "issue",
            "problem",
            "help",
            "complaint",
            "fix",
            "repair",
            "broken",
            "not working",
            "समस्या",
            "परेशानी",
            "मदद",
            "ठीक",
            "काम नहीं",
            "खराब",
        ]
        has_meaningful_content = any(word in text_lower for word in meaningful_words)

        # Only flag as non-grievance if no keywords AND no meaningful content AND text is substantial
        if not has_grievance_keyword and not has_meaningful_content and len(text) > 15:
            return True, "Non-grievance content"

        # Check for bulk submission (if phone number provided)
        if phone_number:
            self.spam_tracker[phone_number].append(text[:50])  # Store first 50 chars
            if len(self.spam_tracker[phone_number]) >= 3:
                # Check similarity of recent submissions
                recent = self.spam_tracker[phone_number][-3:]
                similar_count = 0
                for i in range(len(recent)):
                    for j in range(i + 1, len(recent)):
                        # Simple similarity check
                        if len(set(recent[i].split()) & set(recent[j].split())) > 2:
                            similar_count += 1

                if similar_count >= 2:
                    return True, "Bulk submission"

        return False, None

    def check_up_location(self, location: str) -> bool:
        """Check if the location is in Uttar Pradesh."""
        if not location:
            return False

        location_lower = location.lower()

        # Check PIN code
        pin_match = re.search(r"\b(\d{6})\b", location)
        if pin_match:
            pin_int = int(pin_match.group(1))
            for start, end in self.up_pin_ranges:
                if start <= pin_int <= end:
                    return True
            return False  # PIN code outside UP

        # Check known UP locations
        return any(up_loc in location_lower for up_loc in self.up_locations)

    def determine_completeness(
        self, extracted_data: Dict
    ) -> Tuple[str, List[str], List[str]]:
        """Determine if the grievance is complete or needs follow-up."""
        missing_fields = []
        questions = []
        # Require all fields: name, number, grievance, location, time
        if not extracted_data.get("name"):
            missing_fields.append("name")
            questions.append("May we have your name for updates?")
        if not extracted_data.get("number"):
            missing_fields.append("number")
            questions.append("May we have your phone number for updates?")
        if not extracted_data.get("grievance"):
            missing_fields.append("description")
            questions.append("Please describe your grievance in brief.")
        if not extracted_data.get("location"):
            missing_fields.append("location")
            questions.append("Where is the issue located? (Address/PIN)")
        if not extracted_data.get("time"):
            missing_fields.append("time")
            questions.append("How long has this been ongoing?")
        # Only if all fields are present, it's enough information
        if not missing_fields:
            status = "enough information"
        else:
            status = "follow up needed"
        return status, missing_fields, questions

    def process(self, text: str) -> Optional[Grievance]:
        """Main processing function. Returns Grievance object if not spam, else None."""
        extracted_data = {
            "name": self.extract_name(text, "english"),
            "number": self.extract_phone_number(text),
            "grievance": self.extract_grievance(text, "english"),
            "location": self.extract_location(text, "english"),
            "time": self.extract_time(text, "english"),
        }
        # Post-processing: if name is a city, move to location
        if (
            extracted_data["name"]
            and extracted_data["name"].lower() in self.up_locations
        ):
            if not extracted_data["location"]:
                extracted_data["location"] = extracted_data["name"].title()
            extracted_data["name"] = ""
        # If location is a name, move to name
        if (
            extracted_data["location"]
            and extracted_data["location"].lower() not in self.up_locations
            and not re.search(r"pin", extracted_data["location"], re.IGNORECASE)
        ):
            if not extracted_data["name"]:
                extracted_data["name"] = extracted_data["location"]
                extracted_data["location"] = ""
        # Check spam
        is_spam, spam_reason = self.detect_spam(text, extracted_data["number"])
        if not is_spam and extracted_data["location"]:
            location_check = self.check_up_location(extracted_data["location"])
            if not location_check and len(extracted_data["location"]) > 5:
                is_spam = True
                spam_reason = "Out of UP location"
        if is_spam:
            return None
        # Parse date_time from extracted_data['time']
        date_time = None
        if extracted_data["time"]:
            try:
                date_time = datetime.datetime.strptime(
                    extracted_data["time"], "%d-%m-%y"
                )
            except Exception:
                date_time = None
        # Return Grievance object
        return Grievance(
            caller_name=extracted_data["name"] or "",
            caller_phone_no=extracted_data["number"] or "",
            description=extracted_data["grievance"] or "",
            location=extracted_data["location"] or "",
            date_time=date_time,
        )

    def process_grievance_object(self, grievance: "Grievance") -> Optional["Grievance"]:
        """Process an already-populated Grievance object. Return the object if not spam, else None."""
        # Combine all fields into a single text for spam detection
        combined_text = f"{grievance.caller_name} {grievance.caller_phone_no} {grievance.description} {grievance.location}"
        is_spam, spam_reason = self.detect_spam(
            combined_text, grievance.caller_phone_no
        )
        if not is_spam and grievance.location:
            location_check = self.check_up_location(grievance.location)
            if not location_check and len(grievance.location) > 5:
                is_spam = True
        if is_spam:
            return None
        return grievance

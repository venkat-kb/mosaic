from datetime import datetime, timedelta
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import collections
from typing import Optional

# Import the specific data model from your project
from .models import CaseRecord


class HelplineProcessor:

    def __init__(self, time_threshold_minutes: int = 10, similarity_threshold: float = 0.3):
 
        self.time_threshold = timedelta(minutes=time_threshold_minutes)
        self.similarity_threshold = similarity_threshold

        # Tracks history per phone number. Stores (timestamp, text_vector) tuples.
        self.user_history = collections.defaultdict(list)

        # Vectorizer to convert complaint text into numerical data for comparison.
        self.vectorizer = TfidfVectorizer(stop_words='english')

        # A set of keywords to quickly identify invalid or profane complaints.
        self.invalid_keywords = {
            'buy', 'crypto', 'subscribe', 'free', 'money', 'viagra',
            '#@!%', 'f***', 'sucks'
        }

        # Pre-fit the vectorizer with a dummy corpus to avoid errors on the first run.
        self.vectorizer.fit(["i have not that much water in my house, the village development funds are being misappropriated, factory workers are not getting minimum wage, crop insurance claim has not come back to me yet."])

    def process_grievance_object(self, grievance: CaseRecord) -> Optional[CaseRecord]:

        if self._is_repetitive(grievance):
            print(f"SPAM DETECTED (Repetitive): User '{grievance.phone_no}' sent a similar complaint too recently.")
            return None

        if self._is_invalid(grievance):
            print(f"SPAM DETECTED (Invalid Content): Complaint from '{grievance.phone_no}' contains invalid keywords.")
            return None

        # --- If it's not spam, add it to history for future checks ---
        # The date from the CaseRecord is an ISO format string and needs to be parsed.
        grievance_timestamp = grievance.date
        grievance_vector = self.vectorizer.transform([grievance.detail])

        self.user_history[grievance.phone_no].append((grievance_timestamp, grievance_vector))

        return grievance

    def _is_repetitive(self, grievance: CaseRecord) -> bool:

        user_posts = self.user_history.get(grievance.phone_no, [])
        new_grievance_vector = self.vectorizer.transform([grievance.detail])
        # current_timestamp = datetime.fromisoformat(grievance.date)
        current_timestamp = grievance.date

        # Iterate backwards through the user's recent posts
        for past_timestamp, past_vector in reversed(user_posts):
            # 1. Check if the past post is within the defined time window
            if current_timestamp - past_timestamp < self.time_threshold:
                # 2. If it is, check for text similarity
                similarity = cosine_similarity(new_grievance_vector, past_vector)[0][0]
                if similarity >= self.similarity_threshold:
                    return True  # Found a recent, similar post
            else:
                # History is time-sorted, so we can stop searching early
                break
        return False

    def _is_invalid(self, grievance: CaseRecord) -> bool:
        """
        Checks for correctness/validity spam using a predefined keyword list.
        """
        text_lower = grievance.detail.lower()
        for keyword in self.invalid_keywords:
            if keyword in text_lower:
                return True
        return False
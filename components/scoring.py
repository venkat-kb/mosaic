import spacy
import json
import os

from .models import CaseRecord

# Load spaCy model globally to avoid reloading
nlp = spacy.load("en_core_web_lg")


# Load categories data globally
def load_categories():
    path = os.getcwd()
    with open(f"{path}/data/categories_data.json", "r") as file:
        data = json.load(file)
    return data


# Load all case data to calculate max_thread_len
def get_max_thread_length():
    path = os.getcwd()
    with open(f"{path}/data/case_data.json", "r") as file:
        data = json.load(file)
    return max(len(case["thread"]) for case in data)


# Global variables
categories_data = load_categories()
max_thread_len = get_max_thread_length()
alpha = 0.5


def classify_case_priority_flexible(case: CaseRecord, alpha: float = 0.5) -> CaseRecord:
    """
    Classify a single case with flexible parameters.

    Args:
        case (CaseRecord): The case to classify
        categories_data (list): List of category dictionaries
        max_thread_length (int): Maximum thread length for normalization
        alpha (float): Weight parameter for scoring

    Returns:
        CaseRecord: The case with updated classification values
    """
    case_description = nlp(case.case_detail)

    max_score = 0
    selected_category = None
    total_weights = sum(category["semantic_weight"] for category in categories_data)

    for category in categories_data:
        total_similarity = 0
        keyword_count = len(category["keywords"])

        for keyword in category["keywords"]:
            keyword_nlp = nlp(keyword)
            similarity = case_description.similarity(keyword_nlp)
            total_similarity += similarity

        category_score = total_similarity / keyword_count if keyword_count > 0 else 0

        if category_score > max_score:
            max_score = category_score
            selected_category = category

    case.case_category = (
        selected_category["name"] if selected_category else "uncategorized"
    )

    category_weight = (
        selected_category["semantic_weight"] / total_weights if selected_category else 0
    )

    final_score = (
        (alpha * category_weight)
        + ((1 - alpha) * max_score)
        + (len(case.thread) / max_thread_len)
    )

    case.score = final_score

    if final_score < (2 / 3):
        priority = "low"
    elif final_score < (4 / 3):
        priority = "medium"
    else:
        priority = "high"

    case.priority = priority

    return case

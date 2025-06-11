import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import os


def scoring():
    path = os.getcwd()
    categories = []
    case_data = []
    alpha = 0.5

    # Initialize TF-IDF vectorizer
    vectorizer = TfidfVectorizer(
        stop_words="english",
        lowercase=True,
        ngram_range=(1, 2),  # Include both unigrams and bigrams
        max_features=10000,
    )

    with open(f"{path}/data/categories_data.json", "r") as file:
        data = json.load(file)
        for i in data:
            categories.append(i)

    with open(f"{path}/data/test.json", "r") as file:
        data = json.load(file)
        for case in data:
            case_data.append(case)

    max_thread_len = max(len(case["thread"]) for case in case_data)

    # Prepare all text data for vectorization
    all_texts = []
    case_descriptions = []

    # Collect case descriptions
    for case in case_data:
        case_description = case["case_detail"]
        case_descriptions.append(case_description)
        all_texts.append(case_description)

    # Collect all keywords from categories
    all_keywords = []
    for category in categories:
        for keyword in category["keywords"]:
            all_keywords.append(keyword)
            all_texts.append(keyword)

    # Fit the vectorizer on all texts
    tfidf_matrix = vectorizer.fit_transform(all_texts)

    # Split the matrix back into case descriptions and keywords
    num_cases = len(case_descriptions)
    case_vectors = tfidf_matrix[:num_cases]
    keyword_vectors = tfidf_matrix[num_cases:]

    # Process each case
    for i, case in enumerate(case_data):
        case_vector = case_vectors[i]

        max_score = -1  # Initialize to -1 to ensure at least one category is selected
        selected_category = None
        total_weights = 0
        keyword_start_idx = 0

        # Calculate total weights first
        for category in categories:
            total_weights += category["semantic_weight"]

        # Reset keyword index
        keyword_start_idx = 0

        for category in categories:
            keyword_count = len(category["keywords"])

            if keyword_count == 0:
                category_score = 0
            else:
                # Get vectors for this category's keywords
                category_keyword_vectors = keyword_vectors[
                    keyword_start_idx : keyword_start_idx + keyword_count
                ]

                # Calculate similarities between case and each keyword
                similarities = cosine_similarity(
                    case_vector, category_keyword_vectors
                ).flatten()

                # Average similarity for this category
                category_score = np.mean(similarities)

            if category_score > max_score:
                max_score = category_score
                selected_category = category

            keyword_start_idx += keyword_count

        # If no category was selected (shouldn't happen with max_score = -1), select the first category
        if selected_category is None:
            selected_category = categories[0]
            max_score = 0

        case["case_category"] = selected_category

        category_weight = selected_category["semantic_weight"] / total_weights

        final_score = (
            (alpha * category_weight)
            + ((1 - alpha) * max_score)
            + (len(case["thread"]) / max_thread_len)
        )

        case["score"] = final_score

        priority = ""

        if final_score < (2 / 3):
            priority = "low"
        elif final_score < (4 / 3) and final_score > (2 / 3):
            priority = "medium"
        else:
            priority = "high"

        case["priority"] = priority

    with open(f"{path}/data/test.json", "w") as f:
        json.dump(case_data, f)

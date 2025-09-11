import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import os
from db.supabase import create_supabase_client
from collections import defaultdict


def scoring():
    path = os.getcwd()
    categories = []
    case_data = []
    alpha = 0.5
    supabase = create_supabase_client()
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

    # with open(f"{path}/data/test.json", "r") as file:
    #     data = json.load(file)
    #     for case in data:
    #         case_data.append(case)
    case_data = supabase.table("Complaint").select("*").execute().data
    complaints = supabase.table("Complaint").select("*").neq('case_no', 'sub_reddit_id').execute().data

    group_counts = defaultdict(int)
    for complaint in complaints:
        group_counts[complaint["sub_reddit_id"]] += 1

    if (group_counts):
        maxcount = max(group_counts.values())

    max_thread_len = maxcount

    
    # Prepare all text data for vectorization
    all_texts = []
    case_descriptions = []

    # Collect case descriptions
    for case in case_data:
        case_description = case["detail"]
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
        caseoh = case["case_no"]
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

        supabase.table("Complaint").update({"case_category": selected_category}).eq("case_no", caseoh).execute()

        # case["case_category"] = selected_category

        category_weight = selected_category["semantic_weight"] / total_weights

        len_case = 1

        for c in complaints:
            if c["sub_reddit_id"] == case["case_no"]:
                len_case += 1

        final_score = (
            (alpha * category_weight)
            + ((1 - alpha) * max_score)
            + (len_case) / max_thread_len)
        
        supabase.table("Complaint").update({"score": final_score}).eq("case_no", caseoh).execute()
        # case["score"] = final_score

        priority = ""

        if final_score < (2 / 3):
            priority = "low"
        elif final_score < (4 / 3) and final_score > (2 / 3):
            priority = "medium"
        else:
            priority = "high"

        supabase.table("Complaint").update({"priority": priority}).eq("case_no", caseoh).execute()
        # case["priority"] = priority

    # with open(f"{path}/data/test.json", "w") as f:
    #     json.dump(case_data, f)

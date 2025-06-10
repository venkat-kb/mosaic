import spacy
import json
import os
import numpy as np
import warnings


def has_vector(doc):
    """Check if a spaCy Doc has a meaningful vector representation."""
    return doc.has_vector and not np.allclose(doc.vector, 0)


def safe_similarity(doc1, doc2, default_similarity=0.0):
    """Calculate similarity between two spaCy docs with fallback for empty vectors."""
    if not has_vector(doc1) or not has_vector(doc2):
        return default_similarity

    try:
        return doc1.similarity(doc2)
    except Exception as e:
        print(f"Warning: Similarity calculation failed: {e}")
        return default_similarity


def preprocess_text(text):
    """Clean and preprocess text before NLP processing."""
    if not text or not isinstance(text, str):
        return ""

    # Basic cleaning
    text = text.strip()
    if len(text) < 3:  # Very short texts often don't have meaningful vectors
        return ""

    return text


def scoring():
    path = os.getcwd()

    # Suppress the specific spaCy warning
    warnings.filterwarnings(
        "ignore", message=".*Evaluating Doc.similarity based on empty vectors.*"
    )

    try:
        nlp = spacy.load("en_core_web_lg")
    except OSError:
        print("Error: spaCy model 'en_core_web_lg' not found. Please install it using:")
        print("python -m spacy download en_core_web_lg")
        return

    categories = []
    case_data = []
    alpha = 0.5

    # Load categories data
    try:
        with open(f"{path}/data/categories_data.json", "r", encoding="utf-8") as file:
            data = json.load(file)
            categories = data if isinstance(data, list) else list(data.values())
    except FileNotFoundError:
        print("Error: categories_data.json not found")
        return
    except json.JSONDecodeError:
        print("Error: Invalid JSON in categories_data.json")
        return

    # Load case data
    try:
        with open(f"{path}/data/test.json", "r", encoding="utf-8") as file:
            data = json.load(file)
            case_data = data if isinstance(data, list) else list(data.values())
    except FileNotFoundError:
        print("Error: case_data.json not found")
        return
    except json.JSONDecodeError:
        print("Error: Invalid JSON in case_data.json")
        return

    if not case_data:
        print("Warning: No case data found")
        return

    # Calculate max thread length with error handling
    max_thread_len = 1  # Default to avoid division by zero
    try:
        thread_lengths = [
            len(case.get("thread", [])) for case in case_data if case.get("thread")
        ]
        if thread_lengths:
            max_thread_len = max(thread_lengths)
    except (KeyError, TypeError) as e:
        print(f"Warning: Error calculating max thread length: {e}")

    processed_cases = 0

    for case_idx, case in enumerate(case_data):
        try:
            # Get and preprocess case description
            case_description_raw = case.get("case_detail", "")
            case_description_clean = preprocess_text(case_description_raw)

            if not case_description_clean:
                print(f"Warning: Empty or invalid case description for case {case_idx}")
                case["case_category"] = {"name": "unknown", "semantic_weight": 1}
                case["score"] = 0.0
                case["priority"] = "low"
                continue

            case_description = nlp(case_description_clean)

            if not has_vector(case_description):
                print(
                    f"Warning: Case {case_idx} description has no meaningful vector representation"
                )
                case["case_category"] = {"name": "unknown", "semantic_weight": 1}
                case["score"] = 0.0
                case["priority"] = "low"
                continue

            max_score = 0
            selected_category = None
            total_weights = 0

            # Process each category
            for category in categories:
                if not isinstance(category, dict) or "keywords" not in category:
                    continue

                keywords = category.get("keywords", [])
                semantic_weight = category.get("semantic_weight", 1)
                total_weights += semantic_weight

                if not keywords:
                    continue

                category_similarities = []
                valid_similarities = 0

                # Calculate similarity for each keyword
                for keyword in keywords:
                    keyword_clean = preprocess_text(str(keyword))
                    if not keyword_clean:
                        continue

                    keyword_nlp = nlp(keyword_clean)
                    similarity = safe_similarity(case_description, keyword_nlp, 0.0)

                    if similarity > 0:  # Only count meaningful similarities
                        category_similarities.append(similarity)
                        valid_similarities += 1

                # Calculate category score
                if valid_similarities > 0:
                    category_score = sum(category_similarities) / valid_similarities
                else:
                    category_score = 0.0

                # Update best category
                if category_score > max_score:
                    max_score = category_score
                    selected_category = category

            # Set default category if none found
            if selected_category is None:
                selected_category = {"name": "unknown", "semantic_weight": 1}
                total_weights = max(total_weights, 1)

            case["case_category"] = selected_category

            # Calculate final score
            category_weight = selected_category.get("semantic_weight", 1) / max(
                total_weights, 1
            )
            thread_factor = len(case.get("thread", [])) / max_thread_len

            final_score = (
                (alpha * category_weight) + ((1 - alpha) * max_score) + thread_factor
            )

            case["score"] = final_score

            # Determine priority
            if final_score < (2 / 3):
                priority = "low"
            elif final_score < (4 / 3):
                priority = "medium"
            else:
                priority = "high"

            case["priority"] = priority
            processed_cases += 1

        except Exception as e:
            print(f"Error processing case {case_idx}: {e}")
            # Set default values for failed cases
            case["case_category"] = {"name": "error", "semantic_weight": 1}
            case["score"] = 0.0
            case["priority"] = "low"

    print(f"Successfully processed {processed_cases} out of {len(case_data)} cases")

    # Save results
    try:
        with open(f"{path}/data/test.json", "w", encoding="utf-8") as f:
            json.dump(case_data, f, indent=2, ensure_ascii=False)
        print("Results saved to test.json")
    except Exception as e:
        print(f"Error saving results: {e}")

import spacy
import json

path = os.getcwd()

nlp = spacy.load("en_core_web_lg")

categories = []
case_data = []
alpha = 0.5

with open(f"{path}/data/categories_data.json", "r") as file:
    data = json.load(file)

    for i in data:
        categories.append(i)


with open(f"{path}/data/case_data.json", "r") as file:
    data = json.load(file)

    for case in data:
        case_data.append(case)


max_thread_len = max(len(case["thread"]) for case in case_data)

for case in case_data:
    case_description = case["case_detail"]
    case_description = nlp(case_description)

    max_score = 0
    selected_category = 0
    total_weights = 0

    for category in categories:
        total_similarity = 0
        keyword_count = len(category["keywords"])

        category_similarities = []

        total_weights += category["semantic_weight"]

        for keyword in category["keywords"]:
            keyword_nlp = nlp(keyword)
            similarity = case_description.similarity(keyword_nlp)

            category_similarities.append(similarity)
            total_similarity += similarity

        category_score = total_similarity / keyword_count if keyword_count > 0 else 0

        if category_score > max_score:
            max_score = category_score
            selected_category = category

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

print(case_data)

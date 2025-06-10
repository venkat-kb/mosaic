#this is the one we should probs use, it has sentiment analysis also since problem statement mentioned it
import json
import os
import uuid
import shutil
import numpy as np
# import sniffio
from datetime import datetime, timedelta
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
# from ibm_watsonx_ai.foundation_models import Model
from ibm_watsonx_ai.foundation_models import ModelInference as Model
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams
from ibm_watsonx_ai.foundation_models.utils.enums import ModelTypes
from ibm_watsonx_ai import *  #IAMTokenManager
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from sentence_transformers import SentenceTransformer
import spacy
from components.models import CaseRecord

# ------------- CONFIGURATION ----------------
IBM_API_KEY = "X-ZOoWK-P_FUNQtpoRr_7Q27_erBBnYfjYDj-LLpDF7t" #put ur own in 
IBM_PROJECT_ID = "9af6f191-234c-49b5-adaf-bdd314dbd589" #put ur own in 
IBM_REGION = "us-south"  # or your region
EXISTING_JSON = r"C:\Users\venka\Downloads\mosaic\data\test.json"
SIMILARITY_THRESHOLD = 0.2
DATE_WINDOW = timedelta(days=2)
LLM_WEIGHT = 0.4
TFIDF_WEIGHT = 0.6

# RAW_INPUT = r"C:\Users\venka\Downloads\mosaic\experimentaldata\sample_grievances.json"
# OUTPUT_DIR = r"C:\Users\venka\Downloads\mosaic\sampleoutputs"
# OUTPUT_FILE = "grouped_threads_watsonx.json"

# ------------- IBM Watsonx Setup ----------------
# token_manager = IAMTokenManager(api_key=IBM_API_KEY, url=f"https://iam.cloud.ibm.com/identity/token")
token_manager = IAMAuthenticator(IBM_API_KEY)  
model = Model(
    model_id=ModelTypes.GRANITE_8B_CODE_INSTRUCT,  # You can also use granite or mistral based on your access
    params={GenParams.DECODING_METHOD: "greedy", GenParams.MAX_NEW_TOKENS: 10},
    credentials={"url": f"https://{IBM_REGION}.ml.cloud.ibm.com", "apikey": IBM_API_KEY},
    project_id=IBM_PROJECT_ID
)

# embed_model = Model(
#     model_id="embedding-001",  # Available IBM Embedding model
#     credentials={"url": f"https://{IBM_REGION}.ml.cloud.ibm.com", "apikey": IBM_API_KEY},
#     project_id=IBM_PROJECT_ID
# )

# --------- FILE UTILS ---------------
def move_file_to_directory(file_path, target_dir):
    os.makedirs(target_dir, exist_ok=True)
    filename = os.path.basename(file_path)
    target_path = os.path.join(target_dir, filename)
    shutil.move(file_path, target_path)
    print(f"File moved to: {target_path}")

# ---------- Embedding + Similarity ----------------
# def get_watsonx_embedding(text):
#     response = embed_model.generate(texts=[text])
#     return np.array(response['results'][0]['embedding'])
embedder = SentenceTransformer('all-MiniLM-L6-v2')

def get_local_embedding(text):
    return embedder.encode(text)

def cosine_sim(vec1, vec2):
    return float(np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2)))

# ---------- Sentiment Analysis ----------------
def get_sentiment(text):
    prompt = f"Classify the following grievance description as Positive, Neutral, or Negative:\n\n\"{text}\"\n\nSentiment:"
    result = model.generate_text(prompt=prompt)
    # print(type(result))
    sentiment = result.strip().lower()
    if "positive" in sentiment:
        return "Positive"
    elif "negative" in sentiment:
        return "Negative"
    else:
        return "Neutral"

def subredditting(g):
    # ---------- Load and Parse ----------------
    with open(EXISTING_JSON, 'r', encoding='utf-8') as f:
        existing_cases = json.load(f)
    # with open(RAW_INPUT, 'r', encoding='utf-8') as f:
    #     grievances = json.load(f)

    # for g in grievances:
    g.date_time = datetime.fromisoformat(g.date_time)

    # descriptions = [g['description'] for g in grievances]
    descriptions = g.description

    # TF-IDF similarity
    # vectorizer = TfidfVectorizer()
    # tfidf_matrix = vectorizer.fit_transform(descriptions)
    # tfidf_similarity = cosine_similarity(tfidf_matrix)

    # LLM Embeddings
    print("Fetching embeddings from HuggingFace since we tried watsonx but ibm's embedding-001 is not supported for this environment...")
    embeddings = [get_local_embedding(descriptions)]
    print("Embeddings complete.")

    # ---------- Grouping Threads ---------------
    visited = [False] * len(existing_cases)
    threads = []
    best_case_idx = -1
    best_score=-1

    for idx, case in enumerate(existing_cases):
        if visited[idx]:
            continue
        if case["location"].lower() != g.location.lower():
            continue
        try:
            case_date = datetime.fromisoformat(case["problem_start"])
        except ValueError:
            case_date = datetime.strptime(case["problem_start"], "%Y-%m-%d %H:%M:%S")

        if abs((g.date_time - case_date).days) > DATE_WINDOW.days:
            continue

        tfidf = TfidfVectorizer()
        texts = [case["case_detail"], descriptions]
        tfidf_matrix = tfidf.fit_transform(texts)
        tfidf_score = cosine_similarity(tfidf_matrix)[0][1]

        case_embed = get_local_embedding(case["case_detail"])
        llm_score = cosine_sim(embeddings, case_embed)

        final_score = (TFIDF_WEIGHT * tfidf_score + LLM_WEIGHT * llm_score) / (TFIDF_WEIGHT + LLM_WEIGHT)

        if final_score > best_score and final_score >= SIMILARITY_THRESHOLD:
            best_score = final_score
            best_case_idx = idx

    new_thread_entry = {
    "caller_name": g.caller_name,
    "caller_phone_no": g.caller_phone_no,
    "description": g.description,
    "location": g.location,
    "date_time": g.date_time.isoformat()
    }
    if best_case_idx != -1:
        existing_cases[best_case_idx]["thread"].append(new_thread_entry)
    else:
        case = {
            
                "case_no": str(uuid.uuid4()),
                "case_category": "",
                "case_detail": descriptions,
                "problem_start": g.date_time.isoformat(),
                "location": g.location.lower(),
                "priority": "",
                "score": 0,
                "status": "open",
                "thread": [new_thread_entry
                ]
            
        }
        existing_cases.append(case)
    with open(EXISTING_JSON, "w") as f:
        json.dump(existing_cases, f)
            


        # base = grievances[i]
        # base_embed = embeddings[i]
        # thread_items = [base]
        # visited[i] = True

        # for j in range(idx + 1, len(grievances)):
        #     if visited[j]:
        #         continue
        #     g = grievances[j]
        #     if base['location'].lower() != g['location'].lower():
        #         continue
        #     if abs((base['date_time'] - g['date_time']).days) > DATE_WINDOW.days:
        #         continue

        #     tfidf_score = tfidf_similarity[i][j]
        #     llm_score = cosine_sim(base_embed, embeddings[j])
        #     final_score = (TFIDF_WEIGHT * tfidf_score + LLM_WEIGHT * llm_score) / (TFIDF_WEIGHT + LLM_WEIGHT)

        #     if final_score >= SIMILARITY_THRESHOLD:
        #         thread_items.append(g)
        #         visited[j] = True

        # sentiment_result = get_sentiment(thread_items[0]['description'])

        # Build final thread
        # case = {
        #     "case_no": str(uuid.uuid4()),
        #     "case_category": "General Grievance",
        #     "case_detail": thread_items[0]['description'],
        #     "problem_start": thread_items[0]['date_time'].isoformat(),
        #     "location": thread_items[0]['location'],
        #     "urgency": 1,
        #     "scoring": len(thread_items),
        #     "sentiment": sentiment_result,
        #     "thread": [
        #         {
        #             "caller_name": g["caller_name"],
        #             "caller_phone_no": g["caller_phone_no"],
        #             "description": g["description"],
        #             "location": g["location"],
        #             "date_time": g["date_time"].isoformat()
        #         }
        #         for g in thread_items
        #     ]
        # }

        # threads.append(case)

    # # ---------- Save and Move Output ----------------
    # with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    #     json.dump(threads, f, indent=2, ensure_ascii=False)

# print(f"Thread grouping complete. Output saved to {OUTPUT_FILE}")
# move_file_to_directory(OUTPUT_FILE, OUTPUT_DIR)

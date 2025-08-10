import requests
import os
from dotenv import load_dotenv

load_dotenv()

UDYAT_KEY = os.getenv("UDYAT_KEY")
INFERENCE_KEY = os.getenv("INFERENCE_API_KEY")

# Step 1: Fetch pipeline ID for ASR+NMT
def get_pipeline_id():
    url = "https://meity-auth.ulcacontrib.org/ulca/apis/v0/model/getModelsPipeline"
    headers = {"Content-Type": "application/json", "userID": UDYAT_KEY}
    payload = {
        "pipelineTasks": [
            {"taskType": "asr"},
            {"taskType": "translation"}
        ],
        "pipelineRequestConfig": {
            "pipelineId": None,
            "sourceLanguage": "hi",
            "targetLanguage": "en"
        }
    }
    res = requests.post(url, headers=headers, json=payload)
    return res.json()

# Step 2: Call inference
def run_pipeline(audio_file_path):
    url = "https://dhruva-api.bhashini.gov.in/services/inference/pipeline"
    headers = {"Authorization": INFERENCE_KEY}
    files = {"file": open(audio_file_path, "rb")}
    payload = {
        "pipelineTasks": [
            {
                "taskType": "asr",
                "config": {"language": {"sourceLanguage": "hi"}}
            },
            {
                "taskType": "translation",
                "config": {
                    "language": {"sourceLanguage": "hi", "targetLanguage": "en"}
                }
            }
        ]
    }
    res = requests.post(url, headers=headers, files=files, data={"pipeline": str(payload)})
    return res.json()
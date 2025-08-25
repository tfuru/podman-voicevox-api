import json
import os
from typing import Dict, List, Optional
import base64

DB_FILE = "db.json"

# Job Statuses
JOB_STATUS_PENDING = "PENDING"
JOB_STATUS_RUNNING = "RUNNING"
JOB_STATUS_COMPLETED = "COMPLETED"
JOB_STATUS_FAILED = "FAILED"


def load_data() -> Dict:
    if not os.path.exists(DB_FILE):
        return {"api_keys": {}, "jobs": {}}
    with open(DB_FILE, "r") as f:
        return json.load(f)


def save_data(data: Dict):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=2)


def get_api_keys() -> List[str]:
    data = load_data()
    return list(data.get("api_keys", {}).keys())


def add_api_key(key: str):
    data = load_data()
    if "api_keys" not in data:
        data["api_keys"] = {}
    if key not in data["api_keys"]:
        data["api_keys"][key] = {"origins": []}
        save_data(data)


def delete_api_key(key: str):
    data = load_data()
    if "api_keys" in data and key in data["api_keys"]:
        del data["api_keys"][key]
        save_data(data)


def get_origins_for_key(key: str) -> List[str]:
    data = load_data()
    return data.get("api_keys", {}).get(key, {}).get("origins", [])


def add_origin_for_key(key: str, origin: str):
    data = load_data()
    if key in data.get("api_keys", {}):
        if origin not in data["api_keys"][key]["origins"]:
            data["api_keys"][key]["origins"].append(origin)
            save_data(data)


def delete_origin_for_key(key: str, origin: str):
    data = load_data()
    if key in data.get("api_keys", {}):
        if origin in data["api_keys"][key]["origins"]:
            data["api_keys"][key]["origins"].remove(origin)
            save_data(data)


def get_job_data() -> Dict[str, Dict]:
    data = load_data()
    return data.get("jobs", {})


def save_job_data(jobs: Dict[str, Dict]):
    data = load_data()
    data["jobs"] = jobs
    save_data(data)


def add_job(job_id: str, status: str, payload: Dict):
    jobs = get_job_data()
    jobs[job_id] = {"status": status, "payload": payload}
    save_job_data(jobs)


def get_job(job_id: str) -> Optional[Dict]:
    jobs = get_job_data()
    return jobs.get(job_id)


def update_job_status(job_id: str, status: str, result: Optional[bytes] = None, error: Optional[str] = None):
    jobs = get_job_data()
    if job_id in jobs:
        jobs[job_id]["status"] = status
        if result is not None:
            # Store result as base64 string if it's bytes
            jobs[job_id]["result"] = base64.b64encode(result).decode('utf-8')
        if error is not None:
            jobs[job_id]["error"] = error
        save_job_data(jobs)
import json
import os
from typing import Dict, List, Optional
import base64
import threading
import logging

logger = logging.getLogger(__name__)

DB_FILE = "db.json"
RESULTS_DIR = "results"

# Job Statuses
JOB_STATUS_PENDING = "PENDING"
JOB_STATUS_RUNNING = "RUNNING"
JOB_STATUS_COMPLETED = "COMPLETED"
JOB_STATUS_FAILED = "FAILED"

_lock = threading.RLock()


def load_data() -> Dict:
    with _lock:
        if not os.path.exists(DB_FILE):
            return {"api_keys": {}, "jobs": {}}
        try:
            with open(DB_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode {DB_FILE} JSON: {e}")
            backup_file = f"{DB_FILE}.corrupted"
            try:
                if os.path.exists(DB_FILE):
                    os.replace(DB_FILE, backup_file)
                    logger.error(f"Corrupted database file backed up to {backup_file}")
            except Exception as backup_err:
                logger.error(f"Failed to backup corrupted database file: {backup_err}")
            return {"api_keys": {}, "jobs": {}}


def save_data(data: Dict):
    with _lock:
        temp_file = f"{DB_FILE}.tmp"
        try:
            with open(temp_file, "w") as f:
                json.dump(data, f, indent=2)
            os.replace(temp_file, DB_FILE)
        except Exception as e:
            logger.error(f"Failed to write DB file atomically: {e}")
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception:
                    pass
            raise


def get_api_keys() -> List[str]:
    with _lock:
        data = load_data()
        return list(data.get("api_keys", {}).keys())


def add_api_key(key: str):
    with _lock:
        data = load_data()
        if "api_keys" not in data:
            data["api_keys"] = {}
        if key not in data["api_keys"]:
            data["api_keys"][key] = {"origins": []}
            save_data(data)


def delete_api_key(key: str):
    with _lock:
        data = load_data()
        if "api_keys" in data and key in data["api_keys"]:
            del data["api_keys"][key]
            save_data(data)


def get_origins_for_key(key: str) -> List[str]:
    with _lock:
        data = load_data()
        return data.get("api_keys", {}).get(key, {}).get("origins", [])


def add_origin_for_key(key: str, origin: str):
    with _lock:
        data = load_data()
        if key in data.get("api_keys", {}):
            if origin not in data["api_keys"][key]["origins"]:
                data["api_keys"][key]["origins"].append(origin)
                save_data(data)


def delete_origin_for_key(key: str, origin: str):
    with _lock:
        data = load_data()
        if key in data.get("api_keys", {}):
            if origin in data["api_keys"][key]["origins"]:
                data["api_keys"][key]["origins"].remove(origin)
                save_data(data)


def get_job_data() -> Dict[str, Dict]:
    with _lock:
        data = load_data()
        return data.get("jobs", {})


def save_job_data(jobs: Dict[str, Dict]):
    with _lock:
        data = load_data()
        data["jobs"] = jobs
        save_data(data)


def add_job(job_id: str, status: str, payload: Dict):
    with _lock:
        jobs = get_job_data()
        jobs[job_id] = {"status": status, "payload": payload}
        save_job_data(jobs)


def get_job(job_id: str) -> Optional[Dict]:
    with _lock:
        jobs = get_job_data()
        return jobs.get(job_id)


def save_job_result(job_id: str, result: bytes):
    os.makedirs(RESULTS_DIR, exist_ok=True)
    result_path = os.path.join(RESULTS_DIR, f"{job_id}.bin")
    with open(result_path, "wb") as f:
        f.write(result)


def get_job_result(job_id: str) -> Optional[bytes]:
    result_path = os.path.join(RESULTS_DIR, f"{job_id}.bin")
    if os.path.exists(result_path):
        try:
            with open(result_path, "rb") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to read result file {result_path}: {e}")
            return None
    return None


def update_job_status(job_id: str, status: str, result: Optional[bytes] = None, error: Optional[str] = None):
    with _lock:
        jobs = get_job_data()
        if job_id in jobs:
            jobs[job_id]["status"] = status
            if result is not None:
                save_job_result(job_id, result)
            if error is not None:
                jobs[job_id]["error"] = error
            save_job_data(jobs)
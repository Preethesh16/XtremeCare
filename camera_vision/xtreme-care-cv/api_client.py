# api_client.py — POST results to FastAPI backend for XtremeCare

import requests
from config import API_BASE_URL, PATIENT_ID
from utils import get_timestamp


def post_verification_result(patient_id: str, session: str, status: str,
                              timestamp: str, delay_seconds: int) -> bool:
    """
    POST verification outcome to {API_BASE_URL}/verify-intake.

    Body:
        patient_id, session, status, verified_at, delay_seconds

    Returns True on HTTP 2xx, False on any failure.
    If the backend is unreachable, prints a warning and returns False
    (caller should fall back to SQLite-only logging).
    """
    url = f"{API_BASE_URL}/verify-intake"
    payload = {
        "patient_id": patient_id,
        "session": session,
        "status": status,
        "verified_at": timestamp,
        "delay_seconds": delay_seconds,
    }

    try:
        response = requests.post(url, json=payload, timeout=5)
        response.raise_for_status()
        print(f"[API] POST /verify-intake → {response.status_code} OK")
        return True
    except requests.exceptions.ConnectionError:
        print(f"[API] WARNING: Backend unreachable at {API_BASE_URL}. "
              "Result logged to SQLite only.")
        return False
    except requests.exceptions.Timeout:
        print(f"[API] WARNING: Request to {url} timed out.")
        return False
    except requests.exceptions.HTTPError as e:
        print(f"[API] ERROR: HTTP {e.response.status_code} from {url}: {e}")
        return False
    except Exception as e:
        print(f"[API] ERROR: Unexpected error posting to {url}: {e}")
        return False


def post_dose_event(patient_id: str, session: str, dispensed_at: str) -> bool:
    """
    POST a dose dispense event to {API_BASE_URL}/log-dose.

    Body:
        patient_id, session, dispensed_at

    Returns True on HTTP 2xx, False on any failure.
    """
    url = f"{API_BASE_URL}/log-dose"
    payload = {
        "patient_id": patient_id,
        "session": session,
        "dispensed_at": dispensed_at,
    }

    try:
        response = requests.post(url, json=payload, timeout=5)
        response.raise_for_status()
        print(f"[API] POST /log-dose → {response.status_code} OK")
        return True
    except requests.exceptions.ConnectionError:
        print(f"[API] WARNING: Backend unreachable at {API_BASE_URL}. "
              "Dose event not posted.")
        return False
    except requests.exceptions.Timeout:
        print(f"[API] WARNING: Request to {url} timed out.")
        return False
    except requests.exceptions.HTTPError as e:
        print(f"[API] ERROR: HTTP {e.response.status_code} from {url}: {e}")
        return False
    except Exception as e:
        print(f"[API] ERROR: Unexpected error posting to {url}: {e}")
        return False

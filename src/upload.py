import os
import requests
from dotenv import load_dotenv

# .env laden
load_dotenv()
VIMEO_TOKEN = os.getenv("VIMEO_TOKEN")
if not VIMEO_TOKEN:
    raise RuntimeError("VIMEO_TOKEN is not set. Create a Vimeo access token with 'upload' permissions and place it in .env as VIMEO_TOKEN=<token>.")
BASE_URL = "https://api.vimeo.com"
HEADERS = {
    "Authorization": f"Bearer {VIMEO_TOKEN}",
    "Accept": "application/vnd.vimeo.*+json;version=3.4",
    "Content-Type": "application/json",
}

#Speicher-Helper
def _get_free_bytes() -> int:
    r = requests.get(f"{BASE_URL}/me", headers=HEADERS, timeout=20)
    r.raise_for_status()
    return int(r.json().get("upload_quota", {}).get("space", {}).get("free", 0))

def _delete_oldest_video() -> bool:
    r = requests.get(
        f"{BASE_URL}/me/videos",
        headers=HEADERS,
        params={"sort": "date", "direction": "asc", "per_page": 1, "fields": "uri"},
        timeout=20,
    )
    r.raise_for_status()
    items = r.json().get("data", [])
    if not items:
        return False

    uri = items[0]["uri"]
    print(f"Lösche ältestes Video: {uri}")
    resp = requests.delete(f"{BASE_URL}{uri}", headers=HEADERS, timeout=30)
    if resp.status_code >= 400:
        try:
            print("Vimeo delete error:", resp.status_code, resp.json())
        except Exception:
            print("Vimeo delete error:", resp.status_code, resp.text)
        resp.raise_for_status()
    return True

def _ensure_space_for(file_path: str):
    need = os.path.getsize(file_path)
    while _get_free_bytes() < need:
        deleted = _delete_oldest_video()
        if not deleted:
            raise RuntimeError("Nicht genug Speicher: keine Videos mehr zum Löschen vorhanden.")


def create_upload_session(
    file_path, name="Mein Video", description="Hochgeladen via API"
):
    url = f"{BASE_URL}/me/videos"
    size = os.path.getsize(file_path)
    data = {
        "upload": {"approach": "tus", "size": size},  # Vimeo expects an integer here
        "name": name,
        "description": description,
    }
    r = requests.post(url, headers=HEADERS, json=data)
    if r.status_code >= 400:
      # Print server explanation to help debugging (e.g., invalid field, missing scope)
      try:
          print("Vimeo error:", r.status_code, r.json())
      except Exception:
          print("Vimeo error:", r.status_code, r.text)
      r.raise_for_status()
    response = r.json()
    return response["upload"]["upload_link"], response["uri"]


def activate_review_page(video_uri):
    print("Aktiviere Review-Seite...", flush=True)
    url = f"{BASE_URL}{video_uri}"
    data = {"review_page": {"active": True}}
    r = requests.patch(url, headers=HEADERS, json=data)
    if r.status_code >= 400:
        try:
            print("Vimeo review error:", r.status_code, r.json())
        except Exception:
            print("Vimeo review error:", r.status_code, r.text)
        r.raise_for_status()


def set_privacy(video_uri, view):
    url = f"{BASE_URL}{video_uri}"
    payload = {"privacy": {"view": view}}
    r = requests.patch(url, headers=HEADERS, json=payload)
    if r.status_code >= 400:
        try:
            print("Vimeo privacy error:", r.status_code, r.json())
        except Exception:
            print("Vimeo privacy error:", r.status_code, r.text)
        r.raise_for_status()


def upload_video(file_path, upload_link):
    file_size = os.path.getsize(file_path)
    with open(file_path, "rb") as f:
        tus_headers = {
            "Tus-Resumable": "1.0.0",
            "Upload-Offset": "0",
            "Content-Type": "application/offset+octet-stream",
            "Content-Length": str(file_size),
        }
        r = requests.patch(upload_link, headers=tus_headers, data=f)
        if r.status_code >= 400:
            try:
                print("TUS upload error:", r.status_code, r.json())
            except Exception:
                print("TUS upload error:", r.status_code, r.text)
            r.raise_for_status()


def get_review_link(video_uri):
    url = f"{BASE_URL}{video_uri}"
    r = requests.get(url, headers=HEADERS)
    if r.status_code >= 400:
        try:
            print("Vimeo get error:", r.status_code, r.json())
        except Exception:
            print("Vimeo get error:", r.status_code, r.text)
        r.raise_for_status()
    data = r.json()
    # Prefer review page if available, else normal link
    if isinstance(data.get("review_page"), dict) and data["review_page"].get("active") and data["review_page"].get("link"):
        return data["review_page"]["link"]
    return data.get("link")


def upload(video_path):
    _ensure_space_for(video_path)
    upload_link, video_uri = create_upload_session(video_path)
    upload_video(video_path, upload_link)
    # Try to set privacy to unlisted; if not allowed by account/workspace policy, fall back to anybody
    try:
        set_privacy(video_uri, "unlisted")
    except Exception:
        try:
            set_privacy(video_uri, "anybody")
        except Exception:
            pass
    # Try to activate review page; ignore if not permitted on this plan
    try:
        activate_review_page(video_uri)
        print("activated review link")
    except Exception:
        print("Could not activate review link")
    return get_review_link(video_uri)

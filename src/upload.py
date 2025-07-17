import os
import requests
from dotenv import load_dotenv

# .env laden
load_dotenv()
VIMEO_TOKEN = os.getenv("VIMEO_TOKEN")
BASE_URL = "https://api.vimeo.com"
HEADERS = {
    "Authorization": f"Bearer {VIMEO_TOKEN}",
    "Accept": "application/vnd.vimeo.*+json;version=3.4",
    "Content-Type": "application/json",
}


def create_upload_session(
    file_path, name="Mein Video", description="Hochgeladen via API"
):
    url = f"{BASE_URL}/me/videos"
    size = os.path.getsize(file_path)
    data = {
        "upload": {"approach": "tus", "size": str(size)},
        "name": name,
        "description": description,
        "privacy": {
            "view": "unlisted"  # Nur via Link sichtbar
        },
    }
    r = requests.post(url, headers=HEADERS, json=data)
    r.raise_for_status()
    response = r.json()
    return response["upload"]["upload_link"], response["uri"]


def activate_review_page(video_uri):
    print("Aktiviere Review-Seite...", flush=True)
    url = f"{BASE_URL}{video_uri}"
    data = {"review_page": {"active": True}, "privacy": {"view": "unlisted"}}
    r = requests.patch(url, headers=HEADERS, json=data)
    r.raise_for_status()


def upload_video(file_path, upload_link):
    with open(file_path, "rb") as f:
        tus_headers = {
            "Tus-Resumable": "1.0.0",
            "Upload-Offset": "0",
            "Content-Type": "application/offset+octet-stream",
            "Authorization": f"Bearer {VIMEO_TOKEN}",
        }
        r = requests.patch(upload_link, headers=tus_headers, data=f)
        r.raise_for_status()


def get_review_link(video_uri):
    url = f"{BASE_URL}{video_uri}"
    r = requests.get(url, headers=HEADERS)
    r.raise_for_status()
    data = r.json()
    return data["review_page"]["link"]


def upload(video_path):
    print("Starte Upload...")
    upload_link, video_uri = create_upload_session(video_path)
    upload_video(video_path, upload_link)
    print("Upload abgeschlossen. Erstelle Review-Link...")
    activate_review_page(video_uri)
    return get_review_link(video_uri)

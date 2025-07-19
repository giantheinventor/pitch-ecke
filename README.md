# Pitch Ecke

## VIMEO Account
You need at least a standard Vimeo subscription to host videos with review links.
You need a Vimeo account to comment on videos with review links.

## Usage
- python main.py to **start script**
- `q` → **stop recording & upload**
- wait **30 seconds**, until the review link is active.

## Dependencies
- **Python 3.10+**
- Install python packages:
  ```bash
  pip install -r requirements.txt
- Install ffmpeg
  - Mac:
    ```bash
    brew install ffmpeg
  - Windows:
    - Install from official site https://ffmpeg.org/download.html

## VIMEO API
- Generate an API key with rights to:
  - upload
  - edit
  - private
- Add the key to your .env file
`
VIMEO_TOKEN = "Your Token"
`
- Add the .env to your gitignore file


## Projektstruktur
```text
├── assets/        
├── src/
│   ├── main.py        
│   ├── record.py      
│   ├── upload.py      
│   ├── generate_qr.py 
├── .env               
├── requirements.txt   
└── README.md

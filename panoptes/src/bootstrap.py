import os
import json
from pathlib import Path

from constants import STORAGE_DIR, LOG_FILE, UPLOAD_DIR, FRAMES_DIR

UPLOAD_DIR.mkdir(exist_ok=True)
FRAMES_DIR.mkdir(exist_ok=True)

def prep():
    os.makedirs(STORAGE_DIR, exist_ok=True)

    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w") as f:
            json.dump([], f)

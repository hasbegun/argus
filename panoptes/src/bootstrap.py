import os
import json

from constants import STORAGE_DIR, LOG_FILE

def prep():
    os.makedirs(STORAGE_DIR, exist_ok=True)

    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w") as f:
            json.dump([], f)

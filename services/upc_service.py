import time

import requests

from config import GOUPC_API_KEY, RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW

# Simple in-process rate limiting for Go-UPC API
_last_request_time = None
_request_count = 0


def validate_upc(upc: str):
    """Validate the UPC format and return a cleaned string."""
    try:
        clean_upc = ''.join(filter(str.isdigit, upc))
        int(clean_upc)
        if len(clean_upc) not in [8, 12]:
            return False, "Invalid UPC length. Must be 8 or 12 digits."
        return True, clean_upc
    except (ValueError, TypeError):
        return False, "Invalid UPC format. Must contain only digits."


def call_upc_api(upc: str):
    """Call the Go-UPC API with rate limiting."""
    global _last_request_time, _request_count

    if not GOUPC_API_KEY:
        print("Error: GOUPC_API_KEY not found in environment variables")
        return None

    current_time = time.time()

    if _last_request_time and current_time - _last_request_time > RATE_LIMIT_WINDOW:
        _request_count = 0

    if _request_count >= RATE_LIMIT_REQUESTS:
        wait_time = RATE_LIMIT_WINDOW - (current_time - _last_request_time)
        if wait_time > 0:
            time.sleep(wait_time)
            _request_count = 0

    base_url = 'https://go-upc.com/api/v1/code'

    try:
        url = f"{base_url}/{upc}"
        response = requests.get(
            url,
            headers={
                'Authorization': f'Bearer {GOUPC_API_KEY}',
                'Accept': 'application/json',
            },
            timeout=10,
        )

        _last_request_time = time.time()
        _request_count += 1

        if response.status_code == 429:
            time.sleep(RATE_LIMIT_WINDOW)
            response = requests.get(
                url,
                headers={
                    'Authorization': f'Bearer {GOUPC_API_KEY}',
                    'Accept': 'application/json',
                },
                timeout=10,
            )

        return response
    except requests.exceptions.RequestException as e:
        print(f"API request error: {e}")
        return None

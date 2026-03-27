"""UPC service — validation and Go-UPC API calls."""
import time

import requests
from django.conf import settings

_last_request_time = None
_request_count = 0


def validate_upc(upc: str):
    """Validate UPC format, return (True, cleaned_upc) or (False, error_msg)."""
    try:
        clean_upc = ''.join(filter(str.isdigit, upc))
        int(clean_upc)
        if len(clean_upc) not in [8, 12]:
            return False, 'Invalid UPC length. Must be 8 or 12 digits.'
        return True, clean_upc
    except (ValueError, TypeError):
        return False, 'Invalid UPC format. Must contain only digits.'


def call_upc_api(upc: str):
    """Call the Go-UPC API with simple in-process rate limiting."""
    global _last_request_time, _request_count

    api_key = getattr(settings, 'GOUPC_API_KEY', '')
    if not api_key:
        print('Error: GOUPC_API_KEY not set')
        return None

    rate_limit_requests = getattr(settings, 'RATE_LIMIT_REQUESTS', 1)
    rate_limit_window = getattr(settings, 'RATE_LIMIT_WINDOW', 1)

    current_time = time.time()
    if _last_request_time and current_time - _last_request_time > rate_limit_window:
        _request_count = 0

    if _request_count >= rate_limit_requests:
        wait_time = rate_limit_window - (current_time - _last_request_time)
        if wait_time > 0:
            time.sleep(wait_time)
            _request_count = 0

    url = f'https://go-upc.com/api/v1/code/{upc}'
    headers = {'Authorization': f'Bearer {api_key}', 'Accept': 'application/json'}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        _last_request_time = time.time()
        _request_count += 1

        if response.status_code == 429:
            time.sleep(rate_limit_window)
            response = requests.get(url, headers=headers, timeout=10)

        return response
    except requests.exceptions.RequestException as e:
        print(f'UPC API request error: {e}')
        return None

import time
import requests


def req(url, method="GET", headers=None, json_data=None, retries=3):
    for attempt in range(retries):
        try:
            if method == "POST":
                r = requests.post(url, headers=headers, json=json_data, timeout=15)
            else:
                r = requests.get(url, headers=headers, timeout=12)
            r.raise_for_status()
            return r.json()
        except requests.exceptions.HTTPError as e:
            sc = e.response.status_code
            if sc in (429, 500, 502, 503, 504):
                time.sleep(2 ** attempt)
            else:
                return None
        except Exception:
            time.sleep(2 ** attempt)
    return None
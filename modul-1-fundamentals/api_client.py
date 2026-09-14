"""
Modul 1 Übung: Robuster API-Client

Ziel: fetch_json() soll HTTP-GET-Requests robust genug machen für den
produktiven Einsatz mit LLM-APIs (OpenAI, Anthropic, HF) in Modul 2.

Testbar gegen httpbin.org (kein API-Key nötig):
- https://httpbin.org/json          -> normaler Erfolgsfall
- https://httpbin.org/status/500    -> Server-Fehler, sollte retried werden
- https://httpbin.org/status/404    -> Client-Fehler, sollte NICHT retried werden
- https://httpbin.org/delay/5       -> zum Testen von Timeout-Handling
- https://httpbin.org/status/429    -> Rate-Limit-Fall
"""

import time
import requests


class RetryableError(Exception):
    """Fehler, bei dem ein erneuter Versuch sinnvoll ist (5xx, Timeout, Verbindungsfehler)."""
    pass


class ClientError(Exception):
    """Fehler, bei dem ein erneuter Versuch NICHT sinnvoll ist (4xx außer 429)."""
    pass


def fetch_json(url: str, max_retries: int = 3, timeout: float = 3.0) -> dict:
    for retry in range(max_retries):
        backoff = 1.5**retry
        try:
            response = requests.get(url,timeout=timeout)
            status = response.status_code
            if status >= 500:
                print(f"Status Code = {status}. Retry ... {retry}/{max_retries}")
                continue
            if status >= 400 and status <= 499:
                if status == 429:
                    retry_after = response.headers.get("Retry-After")
                    wait = float(retry_after) if retry_after else backoff
                    time.sleep(wait)
                    continue
                raise ClientError(f"Status: {status}")
            if status == 200:
                print("Status = 200. Ok.")
                try:
                    return response.json()
                except requests.JSONDecodeError:
                    raise ClientError("Invalid JSON detected.")
        except requests.exceptions.Timeout:
            print(f"Connection Timeout. Retry ... {retry}/{max_retries} ")
            time.sleep(backoff)
            continue
        except requests.exceptions.ConnectionError:
            print(f"Connection Error. Retry ... {retry}/{max_retries} ")
            time.sleep(backoff)
            continue
    raise RetryableError(f"Failed after {max_retries} attempts.")


if __name__ == "__main__":
    tests = [
        ("Erfolgsfall", "https://httpbin.org/json"),
        ("Server-Fehler (sollte retryen)", "https://httpbin.org/status/500"),
        ("Client-Fehler (sollte NICHT retryen)", "https://httpbin.org/status/404"),
        ("Timeout-Fall", "https://httpbin.org/delay/5"),
        ("Rate Limit", "https://httpbin.org/status/429"),
    ]

    for label, url in tests:
        print(f"\n--- {label}: {url} ---")
        start = time.time()
        try:
            result = fetch_json(url, max_retries=3, timeout=2.0)
            print(f"OK ({time.time() - start:.1f}s): {result}")
        except (RetryableError, ClientError) as e:
            print(f"Fehler nach {time.time() - start:.1f}s: {e}")

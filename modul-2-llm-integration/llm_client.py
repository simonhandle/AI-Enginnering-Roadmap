"""
Modul 2 Übung: LLM Integration — Groq & HuggingFace im Vergleich

Ziel: denselben Prompt an zwei unterschiedliche APIs schicken und Antwort +
Dauer vergleichen. Beide sprechen das OpenAI Chat-Completions-Format
(gleiche JSON-Struktur), unterscheiden sich aber in Endpoint, Modellname
und Rate Limits.

Setup (vorher in der Shell):
    export GROQ_API="gsk_..."
    export HF_TOKEN="hf_..."

Bearbeite die TODOs der Reihe nach.
"""

import os
import time
import requests
import json

PROVIDERS = {
    "groq": {
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "model": "llama-3.3-70b-versatile",
        "api_key": os.environ.get("GROQ_API"),
    },
    "huggingface": {
        "url": "https://router.huggingface.co/v1/chat/completions",
        # Meta-Modelle sind auf HF oft "gated" (Lizenz muss erst akzeptiert
        # werden). Falls dieses Modell einen 403 wirft: auf huggingface.co
        # nach einem ungated Modell suchen, z.B. Qwen/Qwen2.5-7B-Instruct.
        "model": "meta-llama/Llama-3.1-8B-Instruct",
        "api_key": os.environ.get("HF_TOKEN"),
    },
}
print(repr(PROVIDERS["groq"]["api_key"])[:15])

class RetryableError(Exception):
    pass


class ClientError(Exception):
    pass


def chat(provider: str, messages: list[dict], max_retries: int = 3, timeout: float = 15.0) -> str:

    api_url = PROVIDERS[provider]["url"]

    payload = {
        "model":PROVIDERS[provider]["model"],
        "messages": messages,
        "max_tokens": 150,
        "temperature": 0.7
    }

    api_headers = {
        "Authorization": f"Bearer {PROVIDERS[provider]["api_key"]}",
        "Content-Type": "application/json"
    }

    for retry in range(max_retries):
        backoff = (1.5**retry)
        try:
            response = requests.post(api_url,headers=api_headers,data=json.dumps(payload),timeout=timeout)
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
                    return response.json()["choices"][0]["message"]["content"]
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


def compare(system_prompt: str, user_prompt: str):

    messages = [
        {
            "role":"system",
            "content":system_prompt
        },
        {
            "role":"user",
            "content":user_prompt
        }
    ]

    results = []

    for model in PROVIDERS.keys():
        start = time.time()
        result = chat(model,messages=messages)
        results.append(f"MODEL: {model} TIME: {time.time()-start}s \n{result}\n")
    
    for result in results:
        print(result)
    
    return

if __name__ == "__main__":
    compare(
        system_prompt="Du bist ein präziser Assistent. Antworte in maximal 2 Sätzen.",
        user_prompt="Was ist der Unterschied zwischen Chain-of-Thought Reasoning und einem normalen Prompt?",
    )

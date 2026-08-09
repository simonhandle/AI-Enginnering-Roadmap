"""
Modul 3b Übung — RAG from Scratch

`search_notes` in mcp_server.py findet nur exakte Keyword-Treffer: eine Frage
wie "Wie misst man, wie voll ein Hotel ist?" würde dort NICHTS finden, obwohl
hotel-operations.md inhaltlich genau die Antwort hat — nur eben mit den
Wörtern "Auslastung"/"Occupancy Rate" statt "voll".

RAG (Retrieval-Augmented Generation) löst genau das: statt nach exakten
Wörtern zu suchen, wandeln wir Text in Vektoren (Embeddings) um, die
*Bedeutung* abbilden. Ähnliche Bedeutung -> ähnliche Vektoren -> per
Cosine-Similarity auffindbar, unabhängig von der exakten Wortwahl.

Pipeline (die vier Kernbegriffe aus der Roadmap):
    1. Chunking:   Notizen in kleinere Text-Stücke teilen (hier: pro Absatz).
    2. Embedding:  jeden Chunk (und später die Frage) in einen Vektor
                   umwandeln, mit einem lokalen Sentence-Transformer-Modell
                   (kein API-Call, kein Kosten, läuft komplett offline).
    3. Retrieval:  die Chunks finden, deren Vektor der Frage am ähnlichsten
                   ist (Cosine-Similarity, von Hand berechnet mit numpy).
    4. Generation: die Top-Chunks + die Frage zusammen an ein LLM (Groq)
                   geben -> "beantworte die Frage NUR mit diesem Kontext".

Bearbeite die TODOs der Reihe nach.
"""

import json
import os
from pathlib import Path

import numpy as np
import requests
from sentence_transformers import SentenceTransformer

NOTES_DIR = Path(__file__).parent / "sample_notes"
MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"  # mehrsprachig, klein, läuft lokal

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"


def load_chunks() -> list[dict]:
    """Lädt alle Notizen und teilt sie pro Absatz (Leerzeile) in Chunks.
    Gibt eine Liste von {"text": ..., "source": <dateiname>} zurück."""
    chunks = []
    for path in sorted(NOTES_DIR.glob("*.md")):
        text = path.read_text()
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        for para in paragraphs:
            chunks.append({"text": para, "source": path.name})
    return chunks

def embed_texts(model: SentenceTransformer, texts: list[str]) -> np.ndarray:
    """Wandle `texts` (eine Liste von Strings) in ein numpy-Array von
    Embeddings um. SentenceTransformer-Modelle haben dafür eine einzige
    Methode, die eine Liste von Strings nimmt und ein Array zurückgibt
    (Shape: (len(texts), embedding_dim)) — such in der sentence-transformers
    Doku/den Attributen von `model` danach."""
    embeddings = model.encode(texts,convert_to_numpy=True)
    return embeddings


def top_k_chunks(
    query_embedding: np.ndarray, chunk_embeddings: np.ndarray, chunks: list[dict], k: int = 3
) -> list[dict]:
    """Berechne die Cosine-Similarity zwischen `query_embedding`
    (Shape: (embedding_dim,)) und JEDEM Vektor in `chunk_embeddings`
    (Shape: (n_chunks, embedding_dim)). Cosine-Similarity zweier Vektoren
    a, b:  (a · b) / (||a|| * ||b||)
    Das kannst du für alle Chunks auf einmal vektorisiert mit numpy
    berechnen (kein Python-for-Loop über einzelne Werte nötig).
    
    Gib die `k` Chunks aus `chunks` zurück, deren Similarity am höchsten
    ist (absteigend sortiert). Tipp: np.argsort gibt aufsteigend sortierte
    Indizes zurück."""

    dot_products = query_embedding * chunk_embeddings
    norm_query = np.linalg.norm(query_embedding)
    norm_chunks = np.linalg.norm(chunk_embeddings)

    #print()

    


def call_groq(prompt: str) -> str:
    """Schickt einen einzelnen User-Prompt an Groq, gibt den Antworttext
    zurück. Kein Tool-Calling hier, nur normale Text-Generation."""
    payload = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
    }
    headers = {
        "Authorization": f"Bearer {os.environ.get('GROQ_API')}",
        "Content-Type": "application/json",
    }
    response = requests.post(GROQ_URL, headers=headers, data=json.dumps(payload), timeout=15.0)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


def answer_question(question: str, k: int = 3):
    model = SentenceTransformer(MODEL_NAME)
    chunks = load_chunks()

    chunk_embeddings = embed_texts(model, [c["text"] for c in chunks])
    query_embedding = embed_texts(model, [question])[0]

    top_chunks = top_k_chunks(query_embedding, chunk_embeddings, chunks, k=k)

    print("--- gefundene Chunks ---")
    for c in top_chunks:
        print(f"[{c['source']}] {c['text'][:80]}...")
    print("------------------------")

    # TODO 3: Baue aus `top_chunks` und `question` einen Prompt für Groq und
    # gib die Antwort aus. Wichtig für "echtes RAG" statt Halluzination:
    # der Prompt sollte das Modell anweisen, NUR den gegebenen Kontext zu
    # nutzen (und zu sagen, wenn die Antwort dort nicht drin steht).
    raise NotImplementedError


if __name__ == "__main__":
    # Bewusst OHNE die Wörter "Auslastung"/"Occupancy" formuliert, um zu
    # testen, ob die Embedding-Suche findet, was Keyword-Suche nicht könnte.
    #answer_question("Wie misst man, wie voll ein Hotel ist?")

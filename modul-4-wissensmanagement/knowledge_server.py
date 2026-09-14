"""
Modul 4 — KI-Wissensmanagement: MCP-Server über deinem echten Notizen-Vault

Das ist die Zusammenführung von Modul 3: dieselbe MCP-Server-Mechanik wie in
mcp_server.py (Modul 3), aber `search_notes` (Keyword-Suche) wird ersetzt
durch echte semantische Suche — die Embedding/Retrieval/Generation-Bausteine
aus rag_from_scratch.py (Modul 3b), die du schon gebaut und getestet hast.

Chunking-Strategie (bewusst gewählt, siehe Diskussion): eine Datei = ein
Chunk. Deine Vault-Notizen sind kurz und listenartig — Absatz-Chunking würde
sie in bedeutungsarme Ein-Zeiler zerlegen.

Testen:
    mcp dev knowledge_server.py

In Claude Code registrieren (dann steht `ask_knowledge_base` als Tool bereit):
    claude mcp add knowledge -- <repo>/.venv/bin/python <repo>/modul-4-wissensmanagement/knowledge_server.py
"""

import json
import os
from pathlib import Path

import numpy as np
import requests
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from sentence_transformers import SentenceTransformer

# MCP-Clients (Claude Code, Claude Desktop, mcp dev, ...) starten den Server als
# Subprozess und reichen NICHT die Shell-Umgebung durch — nur HOME, PATH & Co.
# Deshalb lädt der Server seine Keys selbst aus der .env-Datei im Repo-Root.
load_dotenv(Path(__file__).parents[1] / ".api_keys.env")

VAULT_DIR = Path(__file__).parent / "vault"
MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "openai/gpt-oss-120b"

mcp = FastMCP("knowledge-server")
_model = SentenceTransformer(MODEL_NAME)  # einmal beim Start laden, nicht pro Anfrage


# --- Bereits gelöst in rag_from_scratch.py, hier unverändert übernommen ---

def embed_texts(texts: list[str]) -> np.ndarray:
    return _model.encode(texts, convert_to_numpy=True)


def top_k_chunks(
    query_embedding: np.ndarray, chunk_embeddings: np.ndarray, chunks: list[dict], k: int = 3
) -> list[dict]:
    dot_products = chunk_embeddings @ query_embedding
    norm_query = np.linalg.norm(query_embedding)
    norm_chunks = np.linalg.norm(chunk_embeddings, axis=1)
    similarities = np.argsort(dot_products / (norm_chunks * norm_query))[::-1]
    top_indices = similarities[:k]
    return [chunks[i] for i in top_indices]


def call_groq(prompt: str) -> str:
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

# --- Neu für Modul 4 ---

def load_vault_chunks() -> list[dict]:
    """Lädt jede .md-Datei in VAULT_DIR komplett als einen Chunk (kein Split
    nach Absatz, siehe Docstring oben)."""
    chunks = []
    for path in sorted(VAULT_DIR.glob("*.md")):
        text = path.read_text().strip()
        if text:
            chunks.append({"text": text, "source": path.name})
    return chunks


def build_prompt(question: str, context_chunks: list[dict]) -> str:
    """Baut den RAG-Prompt: Kontext-Blöcke mit Quellenangabe + die Frage.
    Das Modell soll NUR den Kontext nutzen und ehrlich sagen, wenn die
    Antwort dort nicht steht (statt zu halluzinieren)."""
    context = "\n\n".join(
        f"[Quelle: {c['source']}]\n{c['text']}" for c in context_chunks
    )
    return (
        "Du bist ein Assistent für meine persönlichen Arbeitsnotizen.\n"
        "Beantworte die Frage AUSSCHLIESSLICH auf Basis des folgenden Kontexts. "
        "Wenn die Antwort dort nicht enthalten ist, sage klar: "
        "'Dazu steht nichts in den Notizen.' Erfinde nichts dazu. "
        "Nenne am Ende, welche Quelle(n) du verwendet hast.\n\n"
        f"KONTEXT:\n{context}\n\n"
        f"FRAGE: {question}"
    )


@mcp.tool()
def ask_knowledge_base(question: str) -> str:
    """Beantwortet eine Frage auf Basis der Notizen im Vault (semantische
    Suche + LLM-Generation)."""
    chunks = load_vault_chunks()
    if not chunks:
        return "Der Vault ist leer — keine .md-Dateien gefunden."

    chunk_embeddings = embed_texts([c["text"] for c in chunks])
    query_embedding = embed_texts([question])[0]

    top_chunks = top_k_chunks(query_embedding, chunk_embeddings, chunks, k=2)

    prompt = build_prompt(question, top_chunks)
    return call_groq(prompt)


if __name__ == "__main__":
    mcp.run()
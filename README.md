# AI Engineering Roadmap

A structured, hands-on learning path for AI engineering — from fundamentals to
production-grade LLM systems — culminating in a personal, RAG-based knowledge
management tool.

Pace: ~3-5h/week, ~10-14 weeks total (rough guideline, not a hard deadline).
Each module ends with a working deliverable, not just theory.

## Modules

### Module 1 — Fundamentals Check (~1 week)

- Refresher: JSON handling, API error handling (retry logic, timeouts, rate limits)
- ML basics as needed for LLM understanding: embeddings, tokenization, rough
  architecture intuition
- No standalone deliverable — groundwork for Module 2

### Module 2 — LLM Integration (~3 weeks)

- System prompts & prompt design (roles, constraints)
- Chain of Thought reasoning
- APIs: OpenAI, Anthropic, HuggingFace open models — deliberately touching all
  three to feel the differences in handling, pricing, and behavior
- Deliverable: a small AI app wrapping all three APIs for comparison
  → foundation for Module 3

### Module 3 — Real Production Systems (~4-5 weeks)

- LangChain: chains, agents, tool-use basics
- RAG: embeddings, vector search, chunking strategies
- Orchestrating multiple API calls robustly (revisiting Module 1's error handling)
- MCP (Model Context Protocol): model ↔ external tool/data interaction
- LLM Ops: monitoring, cost tracking, logging
- Deliverable: extend the Module 2 app with RAG capability (answer questions
  over your own documents) → stepping stone to Module 4

### Module 4 — AI-Powered Knowledge Management (~3-4 weeks)

- Choose and set up a data environment: Obsidian or Notion
- Evaluate cost-efficient inference/compute options (e.g. Nebius)
- Connect the Module 3 RAG pipeline to the chosen data environment
- Deliverable: a personal AI knowledge management tool (MVP) that searches
  your own notes/vault and answers questions via an LLM

## Goals

- Build practical AI engineering skills relevant to integrating AI into
  organizations
- Improve Python programming skills

## Progress

- [x] Module 1 — Fundamentals Check
  - [x] `modul-1-fundamentals/api_client.py` — robust API client (timeout,
    retry with exponential backoff, rate-limit / `Retry-After` handling,
    client vs. server error distinction, malformed JSON handling)
- [x] Module 2 — LLM Integration
  - [x] `modul-2-llm-integration/llm_client.py` — same retry/error-handling
    pattern adapted for POST requests, comparing Groq and HuggingFace
    (free-tier) chat completion APIs side by side
- [x] Module 3 — Real Production Systems
  - [x] `modul-3-production-systems/mcp_server.py` — MCP server (stdio) exposing
    `list_notes`, `read_note`, `search_notes` (keyword search) over
    `sample_notes/`
  - [x] `modul-3-production-systems/mcp_client.py` — minimal MCP client with a
    hand-written agent loop: Groq tool-calling ↔ MCP tool execution
  - [x] `modul-3-production-systems/rag_from_scratch.py` — RAG pipeline without
    frameworks: paragraph chunking, local sentence-transformer embeddings,
    cosine-similarity retrieval in numpy, context-only generation via Groq
- [x] Module 4 — AI-Powered Knowledge Management
  - [x] `modul-4-wissensmanagement/knowledge_server.py` — MCP server over a
    personal Markdown vault (Obsidian-style). One tool, `ask_knowledge_base`,
    runs the Module 3 RAG pipeline: file-level chunking, semantic retrieval,
    answer with source citation (and an explicit "not in the notes" fallback)

## Repository Structure

```
.
├── roadmap.md                   # original German planning notes (not tracked)
├── README.md                    # this file
├── requirements.txt
├── .api_keys.env                # GROQ_API / HF_TOKEN (not tracked)
├── modul-1-fundamentals/
│   └── api_client.py            # Module 1 exercise
├── modul-2-llm-integration/
│   └── llm_client.py            # Module 2 exercise
├── modul-3-production-systems/
│   ├── mcp_server.py            # MCP notes server (keyword search)
│   ├── mcp_client.py            # MCP client + agent loop (Groq tool-calling)
│   ├── rag_from_scratch.py      # embeddings + cosine retrieval + generation
│   └── sample_notes/            # demo notes for Module 3
└── modul-4-wissensmanagement/
    ├── knowledge_server.py      # MCP server: semantic Q&A over the vault
    └── vault/                   # personal notes (not tracked)
```

## Setup & Usage

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Put your keys in `.api_keys.env` (`GROQ_API=...`, `HF_TOKEN=...`). Scripts in
Modules 1–3 read them from the shell environment (`set -a; source
.api_keys.env; set +a`); the Module 4 server loads the file itself, because
MCP clients don't pass the shell environment through to server subprocesses.

```bash
# Module 3b: RAG demo
python modul-3-production-systems/rag_from_scratch.py

# Module 4: inspect the knowledge server in the browser
cd modul-4-wissensmanagement && mcp dev knowledge_server.py

# Module 4: register it as a tool in Claude Code
claude mcp add knowledge -- "$PWD/.venv/bin/python" "$PWD/modul-4-wissensmanagement/knowledge_server.py"
```

Groq model: `openai/gpt-oss-120b` (Groq retires models regularly — a 404
`model_not_found` means it's time to pick a new one from `/openai/v1/models`).

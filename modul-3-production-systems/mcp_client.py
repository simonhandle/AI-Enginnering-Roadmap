"""
Modul 3 Übung — Minimaler MCP-Client mit Agent-Loop

Der MCP Inspector war ein Debug-Tool, bei dem DU das "Modell" warst (Tool
manuell auswählen, Argumente eintippen). Hier schreibst du den echten Client:
ein Skript, das sich mit deinem Notes-Server (mcp_server.py) verbindet, ihm
sagt "hier sind deine Tools" — an ein LLM (Groq) — und dann eine Agent-Loop
fährt:

    1. User-Frage + Liste der verfügbaren Tools an das LLM schicken.
    2. Falls die Antwort "tool_calls" enthält (das LLM will ein Tool
       aufrufen): das Tool wirklich über die MCP-Session ausführen, das
       Ergebnis als neue Nachricht zurück ans LLM geben, zurück zu 1.
    3. Falls die Antwort normaler Text ist (keine tool_calls): fertig,
       ausgeben.

Das ist die Schleife, die hinter jedem "AI Agent" steckt — LangChain,
Claude Code usw. machen im Kern nichts anderes, nur mit mehr Komfort
drumherum. Wenn du das hier einmal selbst geschrieben hast, ist an der
Abstraktion nichts mehr magisch.

Groq unterstützt Tool-Calling im selben OpenAI-kompatiblen Format wie eure
normalen Chat-Completions aus Modul 2 — nur mit einem zusätzlichen "tools"-
Feld im Request und "tool_calls" in der Antwort statt normalem "content".

WICHTIGER GOTCHA: Wenn die Antwort tool_calls enthält, musst du diese
Assistant-Message (so wie sie ist, inkl. tool_calls) selbst auch an
`messages` anhängen, BEVOR du die tool-Ergebnis-Message(s) anhängst. Sonst
beschwert sich die API, dass tool_calls ohne passende Antwort offen sind.

Bearbeite die TODOs der Reihe nach.
"""

import asyncio
import json
import os
import sys
from pathlib import Path

import requests
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "openai/gpt-oss-120b"

SERVER_PARAMS = StdioServerParameters(
    command=sys.executable,  # dasselbe Python (venv), mit dem der Client läuft
    args=["mcp_server.py"],
    cwd=str(Path(__file__).parent),
)


def call_groq(messages: list[dict], tools: list[dict] | None = None) -> dict:
    """Schickt messages (+ optional tools) an Groq, gibt die rohe
    `message` der Antwort zurück (choices[0]["message"], als dict)."""
    payload = {"model": GROQ_MODEL, "messages": messages, "temperature": 0.3}
    if tools:
        payload["tools"] = tools
    headers = {
        "Authorization": f"Bearer {os.environ.get('GROQ_API')}",
        "Content-Type": "application/json",
    }
    response = requests.post(GROQ_URL, headers=headers, data=json.dumps(payload), timeout=15.0)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]


def mcp_tools_to_groq_format(mcp_tools: list) -> list[dict]:
    """
    Wandle die Liste von mcp.types.Tool-Objekten (aus
    session.list_tools()) in das Format um, das Groq/OpenAI im
    "tools"-Feld des Requests erwartet:
    
      {"type": "function", "function": {"name": ..., "description": ...,
       "parameters": ...}}
    
    Jedes Tool-Objekt hat .name, .description, .inputSchema (ein JSON-
    Schema-dict) — welches Feld hier passt wohin?
    """
    tools = []
    for tool in mcp_tools:
        tool_in_groq_format = {
            "type":"function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.inputSchema
            }
        }
        tools.append(tool_in_groq_format)
    return tools


async def run_agent(user_question: str):
    async with stdio_client(SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools_result = await session.list_tools()
            groq_tools = mcp_tools_to_groq_format(tools_result.tools)

            messages = [{"role": "user", "content": user_question}]

            while True:
                message = call_groq(messages, groq_tools)
                if message.get("tool_calls"):
                    messages.append(message)  # siehe GOTCHA oben
                    for call in message["tool_calls"]:
                        name = call["function"]["name"]
                        args = json.loads(call["function"]["arguments"])
                        print(f"TOOL CALL: {name} ({args})")
                        result = await session.call_tool(name, args)
                        print(f"RESULT (voll): {[c.text for c in result.content]}")
                        messages.append({
                              "role": "tool",
                              "tool_call_id": call["id"],
                              "content": f"RESULT (voll): {[c.text for c in result.content]}"
                        })
                    continue
                print(message["content"])
                return


if __name__ == "__main__":
    asyncio.run(run_agent("Steht hier irgendwas über AI?"))

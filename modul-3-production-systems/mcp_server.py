"""
Modul 3 Übung — MCP-Server: Notes-Tools

MCP (Model Context Protocol) ist ein Standard-Protokoll, über das ein LLM-Client
(z.B. Claude Code, Claude Desktop) mit einem separaten Server spricht, der
"Tools" (aufrufbare Funktionen) und "Resources" (lesbare Daten) bereitstellt.
Der Client entscheidet zur Laufzeit, welches Tool es mit welchen Argumenten
aufruft — ähnlich wie bei einer normalen API, nur dass hier das Modell selbst
der "Caller" ist statt deines eigenen Codes.

Transport hier: stdio (der Client startet den Server als Subprozess und redet
über stdin/stdout mit ihm — kein HTTP-Server, kein offener Port).

Ziel dieser Übung: ein MCP-Server, der drei Tools über die Notizen in
sample_notes/ anbietet. Das ist bewusst eine Vorstufe zu Modul 4
(Wissensmanagement) — hier noch mit simpler Keyword-Suche, in Modul 3b
(RAG from scratch) ersetzen wir die Suche durch echte Embeddings.

Testen:
    mcp dev mcp_server.py
        -> startet den MCP Inspector im Browser, dort kannst du die Tools
           einzeln aufrufen und die Rückgabewerte sehen.

    Alternativ als echten MCP-Server in Claude Code registrieren:
        claude mcp add notes -- <pfad-zum-venv>/bin/python <pfad>/mcp_server.py

Bearbeite die TODOs der Reihe nach.
"""

from pathlib import Path
from mcp.server.fastmcp import FastMCP

NOTES_DIR = Path(__file__).parent / "sample_notes"

mcp = FastMCP("notes-server")

@mcp.tool()
def list_notes() -> list[str]:
    """Listet die Dateinamen aller verfügbaren Notizen auf."""

    filenames = []
    paths = NOTES_DIR.glob("*.md")
    for path in paths:
        filenames.append(str(path.name))

    return list(filenames)

@mcp.tool()
def read_note(filename: str) -> str:
    """Gibt den vollständigen Inhalt einer Notiz zurück."""
    file = NOTES_DIR/filename
    if file not in NOTES_DIR.glob("*.md"):
        raise FileNotFoundError
    with open(file) as f:
        content = f.read()
        return str(content)


@mcp.tool()
def search_notes(query: str) -> list[str]:
    """Durchsucht alle Notizen nach `query` und gibt Treffer als
    'dateiname: Zeile' zurück."""
    norm_query = query.lower()
    result = []
    for path in NOTES_DIR.glob("*.md"):
        with open(path,"r") as f:
            for row,content in enumerate(f,start=1):
                if norm_query in content.lower():
                    result.append(f'{path.name}: {content.strip()} (row {row})')

    if not result:
        result.append('Query not found!')
        return result
    return result
    
if __name__ == "__main__":
    mcp.run()

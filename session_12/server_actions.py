"""Given — a second MCP server, same pattern you built in Session 11. This one's
tool changes state (moves a file), so it's annotated destructiveHint=True,
readOnlyHint=False — that's what makes agent.py treat it as consequential and
require human confirmation before calling it. Nothing to implement here; read
it to see what a second server looks like, then focus on agent.py's TODOs.
"""
from pathlib import Path

from mcp.server.mcpserver import MCPServer
from mcp_types import ToolAnnotations
from RPA.FileSystem import FileSystem
from RPA.Tables import Tables

BASE_DIR = Path(__file__).parent
REQUESTS_DIR = BASE_DIR / "requests"
APPROVED_DIR = BASE_DIR / "approved"

mcp_server = MCPServer("club-reimbursements-actions")


@mcp_server.tool(annotations=ToolAnnotations(destructiveHint=True, readOnlyHint=False, idempotentHint=False))
def approve_reimbursement(request_id: str) -> str:
    """Approve a pending reimbursement request by its request_id (e.g. "R301").

    This is a consequential action: it moves the request out of the pending queue
    into the approved ledger. Once approved, it can't be un-approved through this tool.
    """
    fs = FileSystem()
    tables = Tables()
    APPROVED_DIR.mkdir(exist_ok=True)

    for csv_path in sorted(REQUESTS_DIR.glob("*.csv")):
        table = tables.read_table_from_csv(str(csv_path), header=True)
        row = tables.get_table_row(table, 0, as_list=False)
        if row["request_id"] == request_id:
            fs.move_file(str(csv_path), str(APPROVED_DIR / csv_path.name), overwrite=True)
            return f"Approved {request_id} ({row['member_name']}, {row['amount_eur']} EUR)."

    return f"No pending request found with request_id {request_id!r}."


if __name__ == "__main__":
    mcp_server.run(transport="stdio")

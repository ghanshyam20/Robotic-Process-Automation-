"""Given — Session 11's server, unchanged except one addition: the tool is now
explicitly annotated readOnlyHint=True. That annotation is what agent.py checks
to decide a tool never needs human confirmation — see is_consequential in agent.py.
"""
from pathlib import Path

from mcp.server.mcpserver import MCPServer
from mcp_types import ToolAnnotations
from RPA.Tables import Tables

BASE_DIR = Path(__file__).parent
REQUESTS_DIR = BASE_DIR / "requests"

mcp_server = MCPServer("club-reimbursements-lookup")


@mcp_server.tool(annotations=ToolAnnotations(readOnlyHint=True))
def check_pending_reimbursements(category: str | None = None) -> str:
    """Report how many club reimbursement requests are pending and their total amount in EUR.

    Optionally filter to a single budget category (Equipment, Events, Admin, or Consumables).
    Omit category to summarize all pending requests regardless of category.
    """
    tables = Tables()
    csv_files = sorted(REQUESTS_DIR.glob("*.csv"))

    count = 0
    total = 0.0
    for csv_path in csv_files:
        table = tables.read_table_from_csv(str(csv_path), header=True)
        row = tables.get_table_row(table, 0, as_list=False)
        if category and row["category"].lower() != category.lower():
            continue
        count += 1
        total += float(row["amount_eur"])

    label = f" in {category}" if category else ""
    return f"{count} reimbursement request(s) pending{label}, totaling {total:.2f} EUR."


if __name__ == "__main__":
    mcp_server.run(transport="stdio")

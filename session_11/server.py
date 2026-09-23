"""Session 11 exercise: build a minimal MCP server with one tool.

Fill in the TODO inside `check_pending_reimbursements`. Everything around it —
the `@mcp_server.tool()` decorator, the function signature, the docstring — is
already doing real work: this is the entire "protocol mechanics" of exposing a
tool over MCP. The decorator introspects the function's type hints to build the
tool's JSON parameter schema, and uses the docstring as the tool's description —
what an agent (like agent.py) sees when it asks "what tools are available, and
what do they do?" No manual protocol code required.

Run standalone to sanity-check imports: python server.py (it'll just sit there
waiting for a client — Ctrl+C to stop). Normally it's launched automatically by
agent.py or check_solution.py, not run directly.
"""
from pathlib import Path

from mcp.server.mcpserver import MCPServer
from RPA.Tables import Tables

BASE_DIR = Path(__file__).parent
REQUESTS_DIR = BASE_DIR / "requests"

mcp_server = MCPServer("club-reimbursements")
 

@mcp_server.tool()
def check_pending_reimbursements(category: str | None = None) -> str:
    """Report how many club reimbursement requests are pending and their total amount in EUR.

    Optionally filter to a single budget category (Equipment, Events, Admin, or Consumables).
    Omit category to summarize all pending requests regardless of category.
    """
    # TODO:
    # 1. `tables = Tables()` (RPA.Tables, same as Sessions 4/9).
    # 2. List and sort the CSV files in REQUESTS_DIR.
    # 3. For each file: read it with `tables.read_table_from_csv(str(csv_path), header=True)`,
    #    get its one data row with `tables.get_table_row(table, 0, as_list=False)`.
    # 4. If `category` was given and the row's category doesn't match it
    #    (case-insensitively), skip this row — don't count it.
    # 5. Otherwise, count it and add its amount_eur (as a float) to a running total.
    # 6. Return a one-sentence summary string, e.g.
    #    "2 reimbursement request(s) pending in Events, totaling 143.00 EUR."
    #    (mention the category in the sentence only if one was given).
    tables= Tables()
    csv_files=sorted(REQUESTS_DIR.glob("*.csv"))

    count=0
    total=0.0

    for csv_file in csv_files:
        table=tables.read_table_from_csv(str(csv_file), header=True)
        row = tables.get_table_row(table, 0, as_list=False)

        if category and row["category"].lower() != category.lower():
            continue

        count += 1
        total += float(row["amount_eur"])

    if category:
        return f"{count} reimbursement request(s) pending in {category}, totaling {total:.2f} EUR."

    return f"{count} reimbursement request(s) pending, totaling {total:.2f} EUR."

if __name__ == "__main__":
    mcp_server.run(transport="stdio")
 
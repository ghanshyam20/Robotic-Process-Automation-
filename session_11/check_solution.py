"""Checks your MCP server both directly (as a Python function) and through
a real MCP client session (over the actual stdio protocol) — the second
check is what proves your tool is genuinely usable by an MCP client/agent,
not just correct as a plain function.

python check_solution.py
"""
import asyncio
import sys
from pathlib import Path

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

BASE_DIR = Path(__file__).parent
SERVER_SCRIPT = BASE_DIR / "server.py"

checks_passed = 0
checks_total = 0


def check(label, condition):
    global checks_passed, checks_total
    checks_total += 1
    status = "PASS" if condition else "FAIL"
    if condition:
        checks_passed += 1
    print(f"[{status}] {label}")


def check_direct_call():
    import server
    result = server.check_pending_reimbursements()
    check(f"direct call, no filter: {result!r}",
          "5 reimbursement request(s) pending" in result and "224.40 EUR" in result)

    result = server.check_pending_reimbursements(category="Events")
    check(f"direct call, category='Events': {result!r}",
          "2 reimbursement request(s) pending in Events" in result and "143.00 EUR" in result)

    result = server.check_pending_reimbursements(category="Equipment")
    check(f"direct call, category='Equipment': {result!r}",
          "1 reimbursement request(s) pending in Equipment" in result and "42.00 EUR" in result)


async def check_via_mcp_protocol():
    params = StdioServerParameters(command=sys.executable, args=[str(SERVER_SCRIPT)])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools_result = await session.list_tools()
            tool_names = [t.name for t in tools_result.tools]
            check(f"server exposes check_pending_reimbursements as an MCP tool (found: {tool_names})",
                  "check_pending_reimbursements" in tool_names)

            tool = next((t for t in tools_result.tools if t.name == "check_pending_reimbursements"), None)
            check("tool has a non-empty description (becomes the agent's understanding of what it does)",
                  tool is not None and bool(tool.description))
            check("tool's schema declares an optional 'category' parameter",
                  tool is not None and "category" in tool.input_schema.get("properties", {})
                  and "category" not in tool.input_schema.get("required", []))

            result = await session.call_tool("check_pending_reimbursements", {"category": "Admin"})
            text = "\n".join(c.text for c in result.content if hasattr(c, "text"))
            check(f"calling the tool through the real MCP protocol works: {text!r}",
                  "1 reimbursement request(s) pending in Admin" in text and "22.00 EUR" in text)


def main():
    check_direct_call()
    asyncio.run(check_via_mcp_protocol())
    print()
    print(f"{checks_passed}/{checks_total} checks passed")


if __name__ == "__main__":
    main()

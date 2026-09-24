"""Checks your human-in-the-loop gate directly (no LLM involved, so this is fast
and deterministic) by driving confirm_and_call with fake input, plus checks both
servers are independently reachable over the real MCP protocol.

python check_solution.py
"""
import asyncio
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

from agent import confirm_and_call, is_consequential, SERVER_SCRIPTS

BASE_DIR = Path(__file__).parent

checks_passed = 0
checks_total = 0


def check(label, condition):
    global checks_passed, checks_total
    checks_total += 1
    status = "PASS" if condition else "FAIL"
    if condition:
        checks_passed += 1
    print(f"[{status}] {label}")


def fake_tool(read_only=None, destructive=None):
    annotations = SimpleNamespace(read_only_hint=read_only, destructive_hint=destructive)
    return SimpleNamespace(annotations=annotations)


def check_is_consequential():
    check("a tool with readOnlyHint=True is NOT consequential",
          is_consequential(fake_tool(read_only=True)) is False)
    check("a tool with destructiveHint=True is consequential",
          is_consequential(fake_tool(read_only=False, destructive=True)) is True)
    check("a tool with no annotations at all is treated as consequential (safest default)",
          is_consequential(SimpleNamespace(annotations=None)) is True)


class FakeContent:
    def __init__(self, text):
        self.text = text


class FakeResult:
    def __init__(self, text):
        self.content = [FakeContent(text)]


class FakeSession:
    async def call_tool(self, name, args):
        self.called_with = (name, args)
        return FakeResult("tool actually ran")


async def check_confirm_and_call():
    tool = fake_tool(read_only=False, destructive=True)

    session = FakeSession()
    with patch("builtins.input", return_value="y"):
        text, cancelled = await confirm_and_call(session, tool, "approve_reimbursement", {"request_id": "R999"})
    check("confirming (input='y') actually calls the tool",
          cancelled is False and getattr(session, "called_with", None) == ("approve_reimbursement", {"request_id": "R999"}))

    session2 = FakeSession()
    with patch("builtins.input", return_value="n"):
        text, cancelled = await confirm_and_call(session2, tool, "approve_reimbursement", {"request_id": "R999"})
    check("declining (input='n') does NOT call the tool, and reports cancelled=True",
          cancelled is True and not hasattr(session2, "called_with"))

    read_only_tool = fake_tool(read_only=True)
    session3 = FakeSession()
    with patch("builtins.input", side_effect=AssertionError("should not prompt for a read-only tool")):
        text, cancelled = await confirm_and_call(session3, read_only_tool, "check_pending_reimbursements", {})
    check("a read-only tool is called without any confirmation prompt",
          cancelled is False and getattr(session3, "called_with", None) == ("check_pending_reimbursements", {}))


async def check_both_servers_reachable():
    all_tool_names = []
    for script in SERVER_SCRIPTS:
        params = StdioServerParameters(command=sys.executable, args=[str(script)])
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await session.list_tools()
                all_tool_names.extend(t.name for t in tools.tools)
    check(f"both servers are independently reachable and expose their tools (found {all_tool_names})",
          "check_pending_reimbursements" in all_tool_names and "approve_reimbursement" in all_tool_names)


def main():
    check_is_consequential()
    asyncio.run(check_confirm_and_call())
    asyncio.run(check_both_servers_reachable())
    print()
    print(f"{checks_passed}/{checks_total} checks passed")


if __name__ == "__main__":
    main()

"""Session 12 exercise: extend Session 11's agent to two servers, gated by a
human-in-the-loop confirmation step before consequential actions.

Fill in the two TODO functions: `is_consequential` and `confirm_and_call`.
Everything else — connecting to both servers, merging their tools, routing a
tool call to the right server, and the overall loop — is given.

server_lookup.py (Session 11's tool, read-only) and server_actions.py (new:
approve_reimbursement, which moves a file — a real, consequential change) are
both given, unchanged. Read both, in particular their `annotations=` argument
to `@mcp_server.tool(...)` — that's what your two TODO functions need to check.

Run: python agent.py
Check your work: python check_solution.py
"""
import asyncio
import sys
from contextlib import AsyncExitStack
from pathlib import Path

import ollama
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

MODEL = "llama3.1:8b"
BASE_DIR = Path(__file__).parent
SERVER_SCRIPTS = [BASE_DIR / "server_lookup.py", BASE_DIR / "server_actions.py"]


def mcp_tool_to_ollama(tool):
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.input_schema,
        },
    }


def is_consequential(tool):
    """TODO: return True if `tool` should require human confirmation before
    being called, False if it's safe to call automatically.

    `tool.annotations` (or None, if the server didn't set any) has fields
    `read_only_hint` and `destructive_hint` (both `bool | None` — see
    server_lookup.py/server_actions.py for how a server sets them).

    Logic to implement:
    - If there are no annotations at all (`tool.annotations is None`), treat
      the tool as consequential — the safest default when you don't know.
    - If `read_only_hint` is True, the tool is NOT consequential (no prompt needed).
    - Otherwise (destructive_hint is True, or read_only_hint is explicitly
      False, or anything not positively marked read-only), treat it as
      consequential.
    """
    if tool.annotations is None:
        return True

    if tool.annotations.read_only_hint is True:
        return False

    return True


async def confirm_and_call(session, tool, name, args):
    """TODO: if `is_consequential(tool)`, print what's about to happen and ask
    the user to confirm (`input("Proceed? [y/N]: ")`) before calling the tool.
    If they don't type exactly "y" (case-insensitive), the tool must NOT be
    called.

    Return a tuple `(text, cancelled)`:
    - If not consequential, or the user confirmed: call the tool with
      `await session.call_tool(name, args)`, extract its text the same way
      Session 11 did, and return `(text, False)`.
    - If the user declined: return a short message saying so, and `(message, True)`
      — don't call the tool at all.

    Why the caller needs `cancelled` as a separate signal, not just text: see
    `run_agent` below and try the "finish early" idea in the README once your
    two functions are working — it'll show you directly why this matters.
    """
    if is_consequential(tool):
        print(f"About to call {name} with {args}")

        answer=input("Proceed? [y/N]: ")

        if answer.lower() != "y":
            return "Action cancelled by the user.",True

    result=await session.call_tool(name,args)
    text=result.content[0].text
    return text,False


async def connect_all(stack):
    sessions = []
    for script in SERVER_SCRIPTS:
        params = StdioServerParameters(command=sys.executable, args=[str(script)])
        read, write = await stack.enter_async_context(stdio_client(params))
        session = await stack.enter_async_context(ClientSession(read, write))
        await session.initialize()
        sessions.append(session)
    return sessions


async def run_agent(question):
    async with AsyncExitStack() as stack:
        sessions = await connect_all(stack)

        all_tools = []
        tool_session = {}
        tool_obj = {}
        for session in sessions:
            result = await session.list_tools()
            for t in result.tools:
                all_tools.append(mcp_tool_to_ollama(t))
                tool_session[t.name] = session
                tool_obj[t.name] = t
        print(f"Discovered {len(all_tools)} tool(s) across {len(sessions)} server(s): "
              f"{[t['function']['name'] for t in all_tools]}")

        messages = [{"role": "user", "content": question}]
        response = ollama.chat(model=MODEL, messages=messages, tools=all_tools,
                                options={"temperature": 0})

        if not response["message"].get("tool_calls"):
            print("FINAL (no tool call):", response["message"]["content"])
            return

        messages.append(response["message"])
        any_cancelled = False
        for call in response["message"]["tool_calls"]:
            name = call["function"]["name"]
            args = call["function"]["arguments"]
            session = tool_session[name]
            tool = tool_obj[name]
            print(f"Model wants to call {name} with {args}")
            text, cancelled = await confirm_and_call(session, tool, name, args)
            any_cancelled = any_cancelled or cancelled
            messages.append({"role": "tool", "content": text, "tool_name": name})

        if any_cancelled:
            print("FINAL: Action cancelled by the user — nothing was changed.")
            return

        final = ollama.chat(model=MODEL, messages=messages, tools=all_tools,
                             options={"temperature": 0})
        print("FINAL:", final["message"]["content"])


if __name__ == "__main__":
    asyncio.run(run_agent("How many reimbursement requests are pending?"))
    
   

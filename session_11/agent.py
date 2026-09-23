"""Given — this is the "agent" side, not the exercise. Read it, don't rewrite it.

Connects to server.py over MCP, discovers its tools, and hands them to a local
LLM (Ollama) as callable functions. The model decides whether a question needs
a tool call; if it does, this script executes the call through the real MCP
protocol and feeds the result back for a final natural-language answer.

The exercise is server.py's one TODO — once that's implemented, run this file
directly to see the whole loop work end to end: python agent.py
"""
import asyncio
import sys
from pathlib import Path

import ollama
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

MODEL = "llama3.1:8b"
SERVER_SCRIPT = Path(__file__).parent / "server.py"


def mcp_tool_to_ollama(tool):
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.input_schema,
        },
    }


async def run_agent(question):
    params = StdioServerParameters(command=sys.executable, args=[str(SERVER_SCRIPT)])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools_result = await session.list_tools()
            ollama_tools = [mcp_tool_to_ollama(t) for t in tools_result.tools]
            print(f"Discovered {len(ollama_tools)} tool(s): {[t['function']['name'] for t in ollama_tools]}")

            messages = [{"role": "user", "content": question}]
            response = ollama.chat(model=MODEL, messages=messages, tools=ollama_tools,
                                    options={"temperature": 0})
            print("First response tool_calls:", response["message"].get("tool_calls"))

            if not response["message"].get("tool_calls"):
                print("FINAL (no tool call):", response["message"]["content"])
                return

            messages.append(response["message"])
            for call in response["message"]["tool_calls"]:
                name = call["function"]["name"]
                args = call["function"]["arguments"]
                print(f"Calling MCP tool {name} with args {args}")
                result = await session.call_tool(name, args)
                text = "\n".join(c.text for c in result.content if hasattr(c, "text"))
                # tool_name links this result back to the call that requested it — and
                # keeping `tools=ollama_tools` on the follow-up call matters too: without
                # both, llama3.1:8b sometimes ignores the tool result and hallucinates
                # (or emits another tool-call-shaped string) instead of summarizing it.
                # Verified directly — see exercise-solution/README.md.
                messages.append({"role": "tool", "content": text, "tool_name": name})

            final = ollama.chat(model=MODEL, messages=messages, tools=ollama_tools,
                                 options={"temperature": 0})
            print("FINAL:", final["message"]["content"])


if __name__ == "__main__":
    asyncio.run(run_agent("How many reimbursement requests are pending, and what's the total?"))

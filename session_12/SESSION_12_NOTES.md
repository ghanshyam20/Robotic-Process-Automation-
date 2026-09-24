# Session 12 – Two MCP Servers + Human Confirmation

## 1. Main Objective

The goal of Session 12 was to extend the MCP agent from Session 11.

In Session 11, we had one MCP server with a read-only tool.

In Session 12, we have **two MCP servers**:

1. A **lookup server** that only reads data.
2. An **action server** that can change data.

The important new idea is:

> If an AI tool is going to make a real change, the human must confirm it first.

This is called a **Human-in-the-Loop (HITL)** approach.

---

## 2. Project Structure

```text
session_12/
│
├── agent.py
├── server_lookup.py
├── server_actions.py
├── check_solution.py
├── SESSION_12_NOTES.md
│
├── requests/
│   ├── request_301.csv
│   ├── request_302.csv
│   ├── request_303.csv
│   ├── request_304.csv
│   └── request_305.csv
│
└── approved/
    └── approved requests are moved here
```

---

## 3. The Two MCP Servers

### server_lookup.py

This server contains:

```python
check_pending_reimbursements()
```

Its job is only to **read the pending reimbursement requests**.

For example:

```text
How many reimbursement requests are pending?
```

It does not modify any files.

The tool has:

```python
readOnlyHint=True
```

This tells the agent:

```text
This tool only reads information.
No human confirmation is required.
```

---

### server_actions.py

This server contains:

```python
approve_reimbursement(request_id)
```

Example:

```text
Approve reimbursement request R301.
```

This tool makes a real change.

It moves the CSV file:

```text
requests/request_301.csv
        ↓
approved/request_301.csv
```

The tool has these annotations:

```python
destructiveHint=True
readOnlyHint=False
idempotentHint=False
```

The important ones for this exercise are:

```text
destructiveHint=True
→ The tool changes something.

readOnlyHint=False
→ The tool is not read-only.
```

Therefore, the agent must ask the human before running it.

---

## 4. Overall Architecture

```text
                    USER
                      │
                      ▼
                 Ollama LLM
                llama3.1:8b
                      │
                      ▼
                   agent.py
                      │
             discovers both tools
                      │
          ┌───────────┴───────────┐
          │                       │
          ▼                       ▼
 server_lookup.py          server_actions.py
          │                       │
          ▼                       ▼
 check pending             approve request
 reimbursements                   │
          │                       ▼
    READ ONLY              CHANGES FILE
          │                       │
          ▼                       ▼
 No confirmation           Ask human first
                                  │
                            ┌─────┴─────┐
                            │           │
                            y           n
                            │           │
                            ▼           ▼
                       Call tool     Cancel
                            │
                            ▼
                  requests/ → approved/
```

---

## 5. What We Implemented

There were only **two TODO functions** in `agent.py`.

### TODO 1 – is_consequential()

Purpose:

Decide whether a tool needs human confirmation.

Logic:

```text
Does the tool have annotations?
        │
        ├── NO → consequential → confirmation required
        │
        └── YES
              │
              ▼
      read_only_hint == True?
              │
        ┌─────┴─────┐
       YES          NO
        │            │
        ▼            ▼
      SAFE      CONSEQUENTIAL
   no prompt       ask human
```

Implementation:

```python
if tool.annotations is None:
    return True

if tool.annotations.read_only_hint is True:
    return False

return True
```

### Why default to True?

If the agent does not know whether a tool is safe, it uses the safer choice.

```text
Unknown tool
    ↓
Treat as consequential
    ↓
Ask human first
```

---

## 6. TODO 2 – confirm_and_call()

Purpose:

Before executing a consequential tool, ask the human for permission.

Important prompt:

```text
Proceed? [y/N]:
```

### If user types `y`

```text
y
↓
permission granted
↓
session.call_tool(...)
↓
MCP tool executes
↓
cancelled = False
```

### If user types `n`

```text
n
↓
permission denied
↓
tool is NOT called
↓
nothing changes
↓
cancelled = True
```

The important code structure is:

```python
if is_consequential(tool):
    print(f"About to call {name} with {args}")
    answer = input("Proceed? [y/N]: ")

    if answer.lower() != "y":
        return "Action cancelled by the user.", True

result = await session.call_tool(name, args)
text = result.content[0].text
return text, False
```

---

## 7. Why `(text, cancelled)` Is Returned

The function returns two things:

```python
(text, cancelled)
```

Example after successful execution:

```text
("Approved R301 ...", False)
```

Example after cancellation:

```text
("Action cancelled by the user.", True)
```

`run_agent()` checks:

```python
if any_cancelled:
```

If an action was cancelled, the agent stops and prints:

```text
FINAL: Action cancelled by the user — nothing was changed.
```

This prevents the LLM from continuing as if the action had happened.

---

## 8. How Tool Routing Works

The agent connects to both MCP servers:

```python
SERVER_SCRIPTS = [
    BASE_DIR / "server_lookup.py",
    BASE_DIR / "server_actions.py"
]
```

The agent discovers the available tools.

During testing we saw:

```text
Discovered 2 tool(s) across 2 server(s):
['check_pending_reimbursements', 'approve_reimbursement']
```

The model can then choose the correct tool depending on the user's request.

Example:

```text
"How many reimbursement requests are pending?"
                ↓
check_pending_reimbursements
```

Example:

```text
"Approve reimbursement request R301."
                ↓
approve_reimbursement
```

---

## 9. Test 1 – Human Says NO

Command:

```bash
python agent.py
```

Agent wanted:

```text
approve_reimbursement
{'request_id': 'R301'}
```

The agent asked:

```text
Proceed? [y/N]:
```

We entered:

```text
n
```

Result:

```text
FINAL: Action cancelled by the user — nothing was changed.
```

`request_301.csv` remained inside `requests/`.

This proved that the MCP action cannot run without human permission.

---

## 10. Test 2 – Human Says YES

We ran:

```bash
python agent.py
```

Again the agent wanted to approve R301.

This time we entered:

```text
y
```

Result:

```text
request_301.csv
```

was moved from:

```text
requests/
```

to:

```text
approved/
```

The final response also correctly reported that R301 for Aino Korhonen, €17.40, was approved.

---

## 11. Test 3 – Read-Only Tool

We changed the test question to:

```text
How many reimbursement requests are pending?
```

Ollama selected:

```text
check_pending_reimbursements
```

There was **NO**:

```text
Proceed? [y/N]:
```

The tool ran automatically because:

```python
readOnlyHint=True
```

After R301 had already been approved, the result was:

```text
4 reimbursement requests pending
Total = 207.00 EUR
```

This was correct because originally:

```text
Total = 224.40 EUR
```

R301 was:

```text
17.40 EUR
```

Therefore:

```text
224.40 - 17.40 = 207.00 EUR
```

---

## 12. Official Checker

Command:

```bash
python check_solution.py
```

Final result:

```text
7/7 checks passed
```

The checker confirmed:

* Read-only tools are NOT consequential.
* Destructive tools ARE consequential.
* Tools without annotations are treated as consequential.
* Typing `y` allows the tool call.
* Typing `n` prevents the tool call.
* Read-only tools run without confirmation.
* Both MCP servers are independently reachable.

---

## 13. Important Commands

Activate the virtual environment from `session_12`:

```bash
source ../.venv/bin/activate
```

Run the agent:

```bash
python agent.py
```

Run the official tests:

```bash
python check_solution.py
```

See pending requests:

```bash
ls requests
```

See approved requests:

```bash
ls approved
```

See both:

```bash
ls requests approved
```

---

## 14. Session 11 vs Session 12

### Session 11

```text
User
 ↓
Ollama
 ↓
Agent
 ↓
One MCP server
 ↓
Read reimbursement data
```

### Session 12

```text
User
 ↓
Ollama
 ↓
Agent
 ↓
Two MCP servers
 ↓
┌────────────────────┬─────────────────────┐
│ Lookup server      │ Action server       │
│ Read-only          │ Changes state       │
│ No confirmation   │ Human confirmation  │
└────────────────────┴─────────────────────┘
```

The major new concept in Session 12 is therefore:

> **AI can decide which tool it wants to use, but a human keeps control over consequential actions.**

---

## 15. Simple Memory Trick

Remember Session 12 like this:

```text
READ → automatic

CHANGE → ask human

YES → execute

NO → stop

UNKNOWN → ask human
```

Or even shorter:

```text
Read = Safe
Change = Confirm
Unknown = Confirm
```

---

## 16. What I Learned

After this session, I understand:

* How one agent can connect to multiple MCP servers.
* How MCP tools can contain annotations.
* How `readOnlyHint` identifies a read-only tool.
* How `destructiveHint` describes a state-changing tool.
* How to identify consequential actions.
* How to add human confirmation before an AI executes an action.
* How to prevent a tool from running when the user says no.
* How to route different tool calls to different MCP servers.
* How Ollama chooses an MCP tool based on the user's request.
* Why AI agents should use safe defaults when tool behavior is unknown.
* How Human-in-the-Loop makes an agent safer when it can perform real actions.

---

## Final Result

```text
Session 12
Two MCP servers
        +
Ollama agent
        +
Tool annotations
        +
Human-in-the-loop confirmation
        ↓
7/7 checks passed ✅
```

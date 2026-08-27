# Mini Process Definition Document (PDD)

Process name: ______________________________
Author(s): ______________________________     Date: ______________

Document the process **as it happens today (As-Is)** — not how you'd redesign it for a bot.
That design step comes later, once the process is understood.

## 1. Process overview & goal

- What is this process for? What's the end goal when it completes successfully?
- Who are the actors involved (roles, not names)?

```


```

## 2. As-Is steps

Number each step. One actor and one action per step — if a step description needs "and," it's
probably two steps.

| # | Actor | Action |
|---|-------|--------|
| 1 | | |
| 2 | | |
| 3 | | |
| 4 | | |
| 5 | | |
| 6 | | |
| 7 | | |
| 8 | | |

## 3. Business rules & decision points

For each point where the process branches, state the rule and both paths.

- Decision point: ______________________________
  - Rule: ______________________________
  - Path A: ______________________________
  - Path B: ______________________________

## 4. Exceptions

**Business exceptions** — valid-but-different paths through the real process (e.g. "amount
exceeds approval threshold"). These are legitimate outcomes, not failures.

```


```

**Application exceptions** — something breaking (e.g. a system is unreachable, a file is
corrupt/unreadable). These need a defined fallback, even if the fallback is "stop and notify a
human."

```


```

## 5. In scope / out of scope for RPA

- In scope (a bot could plausibly do this step, as described):
```


```
- Out of scope (requires human judgment, or isn't a good candidate — say why):
```


```

## 6. Volumes, frequency & systems touched

- Volume: how many instances of this process run, per what time period?
- Frequency: how often does it need to run (continuously, daily, on-demand)?
- Systems touched: list every system/application a human interacts with to complete this process.

```


```

# AgentWill — Decision Loop

> This document is a complete walkthrough of how Will thinks, decides, and acts. Every autonomous decision Will makes passes through this loop. Read this document top to bottom to fully understand how an OpenClaw agent operates.

---

## Overview

Will's decision loop is the core of his autonomy. It runs continuously until either the $50,000/month MRR target is reached or Will halts himself. Every iteration of the loop follows the same sequence:

```
context built → LLM called → JSON parsed → action executed → state saved → repeat
```

The loop lives in `run()` inside `agent_will.py` and calls three key methods in sequence:

```
run()
 └── make_decision()
      └── _build_system_prompt()
 └── execute_action()
 └── save_state()
```

---

## Step 1 — Context is Built

At the start of every loop iteration, `run()` checks if `action_queue` is empty.

**If action_queue is empty:**
Will needs to decide what to do next. A context string is built from current state:

```python
context = (
    f"Current objective: {current_objective}. "
    f"Current MRR: ${self.budget_manager.mrr:.2f}. "
    f"Budget: ${current_budget:.2f}. "
    f"Phase: {self.phase}. "
    f"Selected niche: {self.state.get('selected_niche', 'Not yet identified')}. "
    f"What is the single best action to take right now to make progress toward the current objective?"
)
```

This context string is passed to `make_decision()` as the user message.

**If action_queue is non-empty:**
Will skips the LLM call entirely and executes the next queued action. This is how Will chains multiple actions together without burning API calls — for example, after `perform_market_research` completes, `move_to_next_objective` is queued automatically and executes on the next loop iteration without asking the LLM.

---

## Step 2 — System Prompt is Built

`make_decision()` calls `_build_system_prompt()` before every LLM call. The system prompt is rebuilt fresh on every call — it always reflects Will's exact current state.

The system prompt has five sections:

### Section 1 — Identity and Objective
```
You are Will, a fully autonomous AI business agent running on a Mac Mini.
Your sole objective is to reach $50,000/month in MRR starting from $0, completely autonomously.
```

### Section 2 — Current State
```
Current State:
- Phase: Seed
- MRR: $0.00
- Budget: $10,000.00
- Current Objective: Identify a viable market niche
- Selected Niche: Not yet identified
```

### Section 3 — Research Findings (injected only if last_research is non-empty)
```
Last research findings:
- Web results: 10 results for query: "market trends, unmet needs, competitor analysis"
- Web snippets: snippet1 | snippet2 | snippet3
- Social results: 47 total results across Reddit, Twitter/X, HackerNews, ProductHunt
- If niche not yet selected, use select_niche action with your best niche choice based on these findings.
```

This section is the feedback loop — research results flow from `state['last_research']` directly into the next LLM call. Will reads what he found and acts on it.

### Section 4 — Available Actions
```
Available agent actions:
- perform_market_research: Search web and social platforms for market trends and pain points
- select_niche: Commit to a specific business niche based on research findings
- design_and_build_mvp: Design and build the MVP for the selected niche
- launch_marketing_campaign: Launch a marketing campaign to acquire customers
- optimize_and_scale: Optimize operations and scale revenue
- analyze_performance: Analyze current performance data and metrics
- evaluate_current_strategy: Evaluate and reassess current strategy
- generate_marketing_content: Generate marketing copy and content
- move_to_next_objective: Advance to the next business objective
```

### Section 5 — Response Format and Ethical Constraints
```
You must respond with ONLY a valid JSON object in this exact format, no preamble, no explanation:
{"tool": "agent_action", "tool_input": {"action_name": "action_name_here"}}

For select_niche, use this format:
{"tool": "agent_action", "tool_input": {"action_name": "select_niche", "niche": "your chosen niche here"}}

Ethical constraints you must always follow:
- Do not engage in deceptive marketing practices.
- Respect user privacy and data security.
- Operate within all applicable local and international laws.
- Prioritize long-term value creation over short-term gains.
```

---

## Step 3 — Claude API is Called

With the system prompt built, `make_decision()` calls the Claude API:

```python
response = self.client.messages.create(
    model=OPENCLAW_MODEL,       # claude-sonnet-4-6
    max_tokens=256,             # decisions are short JSON objects
    system=self._build_system_prompt(),
    messages=[{"role": "user", "content": context}]
)
```

`max_tokens=256` is intentional — Will's responses are always short JSON objects. Keeping max_tokens low reduces latency and cost per decision cycle.

---

## Step 4 — Response is Parsed and Validated

The raw response text is extracted and cleaned:

```python
raw = response.content[0].text.strip()

# Strip markdown code fences if present
if raw.startswith("```"):
    raw = raw.split("```")[1]
    if raw.startswith("json"):
        raw = raw[4:]
    raw = raw.strip()

decision = json.loads(raw)

# Validate structure
if "tool" not in decision or "tool_input" not in decision:
    raise ValueError(f"Invalid decision structure: {decision}")
```

**Expected response format:**
```json
{"tool": "agent_action", "tool_input": {"action_name": "perform_market_research"}}
```

**For select_niche:**
```json
{"tool": "agent_action", "tool_input": {"action_name": "select_niche", "niche": "AI writing tools for solopreneurs"}}
```

---

## Step 5 — Fallback Behavior

If the LLM response cannot be parsed or fails validation, Will does not crash. He falls back gracefully:

```python
except json.JSONDecodeError as e:
    # LLM returned something that isn't valid JSON
    return {"tool": "agent_action", "tool_input": {"action_name": "evaluate_current_strategy"}}

except Exception as e:
    # Any other failure — API timeout, rate limit, etc.
    return {"tool": "agent_action", "tool_input": {"action_name": "evaluate_current_strategy"}}
```

`evaluate_current_strategy` is the safe fallback — it triggers `analyze_performance` which is always safe to run and generates useful state without spending budget.

---

## Step 6 — Action is Executed

`execute_action()` receives the decision dict and routes to the correct handler:

```python
action = action_input.get("action_name")

if action == "perform_market_research":   # run web + social search
elif action == "select_niche":            # commit niche to state.json
elif action == "design_and_build_mvp":   # deduct MVP cost, mark MVP built
elif action == "generate_marketing_content": # generate copy via content_generator
elif action == "analyze_performance":    # run data_analyzer, get recommendations
elif action == "launch_marketing_campaign":  # deduct cost, simulate MRR gain
elif action == "optimize_and_scale":     # deduct cost, simulate larger MRR gain
elif action == "evaluate_current_strategy":  # queue analyze_performance
elif action == "move_to_next_objective": # increment current_objective_index
elif action == "mission_accomplished":   # log success, return False to halt loop
```

Every handler returns `True` to continue the loop or `False` to halt it. Only `mission_accomplished` returns `False`.

### Action Chaining

Most actions queue a follow-up action before returning. This is how Will chains logical sequences without calling the LLM for every step:

```
perform_market_research
    └── queues: move_to_next_objective

select_niche
    └── queues: move_to_next_objective

design_and_build_mvp (success)
    └── queues: move_to_next_objective

launch_marketing_campaign (success or failure)
    └── queues: evaluate_current_strategy

optimize_and_scale
    └── queues: evaluate_current_strategy (or mission_accomplished if MRR >= target)

evaluate_current_strategy
    └── queues: analyze_performance

analyze_performance
    └── queues: move_to_next_objective (if phase_progression == 'advance')
    └── queues: generate_marketing_content (if A/B testing recommended)
    └── queues: launch_marketing_campaign (if customer acquisition recommended)
```

---

## Step 7 — State is Saved

After every action, `save_state()` writes the full current state to `state.json`:

```python
def save_state(self):
    self.state['phase'] = self.phase
    self.state['current_objective_index'] = self.current_objective_index
    self.state['action_queue'] = list(self.action_queue)
    self.state['mrr_history'] = list(self.mrr_history)
    with open(STATE_FILE, 'w') as f:
        json.dump(self.state, f, indent=4)
```

This means if Will is interrupted at any point — power cut, crash, manual stop — he restores exactly where he was on next boot. The `action_queue` is persisted so even mid-sequence chains resume correctly.

---

## Step 8 — Stuck Detection

After `save_state()`, Will checks if he's stuck:

```python
if self.current_objective_index >= 2 and \
   len(self.mrr_history) == self.mrr_history.maxlen and \
   all(mrr == self.mrr_history[0] for mrr in self.mrr_history):
    self.log_action("Agent seems stuck: MRR has not changed for 5 consecutive actions.", outcome="Halted")
    executable = False
```

**Three conditions must all be true to trigger stuck detection:**
1. Will is past objective index 2 — niche selected and MVP built
2. `mrr_history` is full — at least 5 actions have been taken
3. All 5 MRR values are identical — no revenue movement whatsoever

If stuck, Will halts cleanly and logs the reason. Run `make reset` to restart or manually adjust `state.json` to resume from a different point.

---

## Step 9 — Sleep and Repeat

```python
time.sleep(0.5)
```

0.5 second pause between loop iterations. This prevents hammering the Claude API on rapid action queue flushes and gives logs a readable timestamp spread.

---

## Full Loop Example — First Boot

Here is exactly what happens the first time you run `python agent_will.py`:

```
1.  AgentWill.__init__()
    → load_state()              reads state.json
                                phase: "Initialization"
                                current_objective_index: 0
                                selected_niche: null
                                action_queue: []

2.  run()
    → action_queue is empty
    → build context:
      "Current objective: Identify a viable market niche.
       Current MRR: $0.00. Budget: $10,000.00. Phase: Seed.
       Selected niche: Not yet identified.
       What is the single best action to take right now?"

3.  make_decision()
    → _build_system_prompt()    builds full prompt with state
    → Claude API call           claude-sonnet-4-6, max_tokens=256
    → raw response:             {"tool": "agent_action", "tool_input": {"action_name": "perform_market_research"}}
    → JSON parsed ✓
    → decision returned

4.  execute_action()
    → action: perform_market_research
    → deduct market_research_cost from budget
    → web_search.execute()      searches Serper API
    → social_research.execute() scans Reddit, Twitter/X, HN, ProductHunt
    → state['last_research'] = {web: results, social: social_results}
    → save_state()              research saved to state.json
    → queue: move_to_next_objective

5.  save_state()                full state written to state.json

6.  sleep(0.5)

7.  Loop iteration 2
    → action_queue: [move_to_next_objective]
    → skip LLM call
    → execute move_to_next_objective
    → current_objective_index: 0 → 1
    → log: "Moving to next objective: Develop an MVP"

8.  save_state()

9.  sleep(0.5)

10. Loop iteration 3
    → action_queue is empty
    → build context:
      "Current objective: Develop an MVP.
       Current MRR: $0.00. Budget: $9,950.00. Phase: Seed.
       Selected niche: Not yet identified.
       What is the single best action to take right now?"
    → last_research is now non-empty → injected into system prompt
    → Claude sees research snippets → decides to call select_niche
    → raw response: {"tool": "agent_action", "tool_input": {"action_name": "select_niche", "niche": "AI writing tools for solopreneurs"}}

11. execute_action()
    → action: select_niche
    → state['selected_niche'] = "AI writing tools for solopreneurs"
    → save_state()
    → queue: move_to_next_objective
    → log: "Niche selected: AI writing tools for solopreneurs"

...and so on autonomously.
```

---

## Loop Termination Conditions

The loop ends under three conditions:

| Condition | How it happens | Log entry |
|---|---|---|
| Target reached | `budget_manager.mrr >= TARGET_REVENUE` | "Target MRR achieved! AgentWill operation concluded." |
| Mission accomplished | `execute_action()` returns `False` | "Will has achieved its goal: $50,000.00 MRR!" |
| Stuck detected | MRR unchanged for 5 consecutive actions | "Agent seems stuck: MRR has not changed for 5 consecutive actions." |

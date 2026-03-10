# AgentWill -- Architecture

> This document explains how every file in the AgentWill repo connects, how data flows through the system, and how Will makes autonomous decisions.

---

## Directory Structure
```
agentwill/
├── logs/
│   ├── .gitkeep              # Keeps logs/ in version control without committing log files
│   ├── agent_will.log        # Runtime log -- every action Will takes, JSONL format
│   └── heartbeat.log         # Heartbeat monitor log -- uptime checks
├── tools/
│   ├── web_search.py         # Serper API wrapper -- searches the web for market research
│   ├── content_generator.py  # Generates marketing copy and slogans
│   ├── data_analyzer.py      # Analyzes MRR, CAC, LTV, churn, and conversion metrics
│   ├── budget_manager.py     # Tracks budget, MRR, phase progression, and spending
│   ├── social_research.py    # Scans Reddit, Twitter/X, HackerNews, ProductHunt
│   └── heartbeat.py          # Monitors agent uptime, sends Discord/Telegram alerts
├── .env.example              # All environment variables documented with comments
├── .gitignore                # Excludes .env, state.json, and log files from version control
├── LICENSE                   # MIT
├── Makefile                  # make run, make logs, make state, make reset, make lint
├── README.md                 # Public-facing project overview and quickstart
├── agent_will.py             # Core agent -- decision loop, action execution, state management
├── config.py                 # All constants and environment variable loading
├── requirements.txt          # All Python dependencies
└── state.json                # Runtime state -- persists across restarts, never committed
```

---

## Core Files

### `agent_will.py`
The brain. Contains the `AgentWill` class with four key methods:

| Method | Purpose |
|---|
| `load_state()` | Reads `state.json` on boot, restores Will's last known state |
| `save_state()` | Writes current state to `state.json` after every action |
| `_build_system_prompt()` | Constructs the LLM system prompt with phase, MRR, budget, niche, and research |
| `make_decision()` | Calls Claude API, parses JSON response, returns next action |
| `execute_action()` | Executes the chosen action, updates budget/MRR, queues next action |
| `run()` | Main loop -- runs until TARGET_REVENUE is reached or agent halts |

### `config.py`
Single source of truth for all constants and environment variables. Everything `agent_will.py` needs is imported from here. All required API keys are validated on boot -- Will raises `EnvironmentError` immediately if any required key is missing.

### `state.json`
Will's memory. Written after every action. Contains:
- `phase` -- current business phase
- `current_objective_index` -- which objective Will is working on
- `selected_niche` -- the niche Will committed to after market research
- `last_research` -- raw results from the last web and social search, injected into LLM prompts
- `action_queue` -- pending actions to execute before calling LLM again
- `mrr_history` -- last 5 MRR values, used for stuck detection
- `exit_prep_triggered` -- manual flag to trigger Exit Prep phase
- `milestones` -- timestamps of major revenue events

---

## Tool Architecture

Each tool in `tools/` follows the same interface pattern:
```python
class ToolName:
    def __init__(self):          # Load API keys, configure logging
    def execute(self, ...):      # Main entry point called by agent_will.py
    def get_tool_schema(self):   # OpenClaw tool schema for LLM tool use
```

### Tool Dependency Map
```
agent_will.py
├── tools/web_search.py         -> WEB_SEARCH_API_KEY (Serper)
├── tools/content_generator.py  -> ANTHROPIC_API_KEY
├── tools/data_analyzer.py      -> no external API
├── tools/budget_manager.py     -> no external API
├── tools/social_research.py    -> WEB_SEARCH_API_KEY (Serper) + RAPIDAPI_KEY (optional)
└── tools/heartbeat.py          -> DISCORD_WEBHOOK_URL + TELEGRAM_BOT_TOKEN (both optional)
```

---

## The Decision Loop
```
┌─────────────────────────────────────────────────────────┐
│                     run() -- main loop                  │
│                                                         │
│  1. Is action_queue empty?                              │
│     YES -> build context string -> call make_decision() │
│     NO  -> skip LLM call, use queued action             │
│                 |                                       │
│  2. make_decision()                                     │
│     -> check phase via check_budget_status()            │
│     -> check if MRR >= TARGET_REVENUE                   │
│     -> call _build_system_prompt()                      │
│     -> call Claude API (claude-sonnet-4-6)              │
│     -> parse JSON response                              │
│     -> validate structure                               │
│     -> return action dict                               │
│                 |                                       │
│  3. execute_action()                                    │
│     -> look up phase_config from budget_manager         │
│     -> execute chosen action (research, campaign, etc.) │
│     -> update budget/MRR                                │
│     -> queue next logical action                        │
│     -> return True (continue) or False (halt)           │
│                 |                                       │
│  4. save_state()                                        │
│     -> write all state to state.json                    │
│                 |                                       │
│  5. Stuck detection                                     │
│     -> if MRR unchanged for 5 consecutive actions       │
│     -> halt with "Agent seems stuck" log entry          │
│                 |                                       │
│  6. sleep(0.5) -> repeat                                │
└─────────────────────────────────────────────────────────┘
```

---

## System Prompt Architecture

Every call to `make_decision()` builds a fresh system prompt via `_build_system_prompt()`. The prompt injects:
```
You are Will, a fully autonomous AI business agent...

Current State:
- Phase: {self.phase}
- MRR: ${self.budget_manager.mrr}
- Budget: ${self.budget_manager.current_budget}
- Current Objective: {self.objectives[self.current_objective_index]}
- Selected Niche: {self.state.get('selected_niche')}

Last research findings:
- Web results: N results for query: "..."
- Web snippets: snippet1 | snippet2 | snippet3
- Social results: N total results across Reddit, Twitter/X, HackerNews, ProductHunt

Available agent actions:
- perform_market_research
- select_niche
- design_and_build_mvp
- launch_marketing_campaign
- optimize_and_scale
- analyze_performance
- evaluate_current_strategy
- generate_marketing_content
- move_to_next_objective

Respond with ONLY a valid JSON object...

Ethical constraints...
```

The LLM responds with a single JSON object:
```json
{"tool": "agent_action", "tool_input": {"action_name": "perform_market_research"}}
```

For `select_niche`, the LLM includes the niche name:
```json
{"tool": "agent_action", "tool_input": {"action_name": "select_niche", "niche": "AI writing tools for solopreneurs"}}
```

---

## Research -> Decision Feedback Loop
```
perform_market_research()
    |
    ├── web_search.execute()        -> returns results dict
    └── social_research.execute()   -> returns results dict
    |
    └── state['last_research'] = {
            'web': results,
            'social': social_results
        }
        save_state()
            |
            └── next make_decision() call
                    |
                    └── _build_system_prompt()
                            |
                            └── injects web snippets + social result count
                                into system prompt
                                    |
                                    └── LLM reasons about findings
                                        -> calls select_niche with
                                           informed niche choice
```

---

## Phase Progression

| Phase | MRR Threshold | Key Behavior |
|---|
| Seed | $0 | Focus on market research and niche selection |
| Pre-Seed | $100 | MVP development, early marketing |
| Series A | $1,000 | Customer acquisition campaigns |
| Series B | $10,000 | Optimization and scaling |
| Series C | $25,000 | Aggressive scaling |
| IPO | $50,000 | Revenue consolidation |
| Exit Prep | Manual only | Business listing and sale preparation |

---

## Stuck Detection

Will monitors his own progress. If `current_objective_index >= 2` and MRR has not changed for 5 consecutive actions, Will logs a `"Agent seems stuck"` entry and halts.

---

## Restart Behavior

Will is designed to restart cleanly. On boot:
1. `load_state()` reads `state.json`
2. All previous state is restored -- phase, objective, niche, research, action queue
3. If `action_queue` is non-empty, Will resumes mid-sequence without calling the LLM
4. If `action_queue` is empty, Will calls `make_decision()` with full context including previous research

Run `make reset` to wipe state and start Will from scratch.
# AgentWill â Architecture

> This document explains how every file in the AgentWill repo connects, how data flows through the system, and how Will makes autonomous decisions.

---

## Directory Structure
```
agentwill/
âââ logs/
â   âââ .gitkeep              # Keeps logs/ in version control without committing log files
â   âââ agent_will.log        # Runtime log â every action Will takes, JSONL format
â   âââ heartbeat.log         # Heartbeat monitor log â uptime checks
âââ tools/
â   âââ web_search.py         # Serper API wrapper â searches the web for market research
â   âââ content_generator.py  # Generates marketing copy and slogans
â   âââ data_analyzer.py      # Analyzes MRR, CAC, LTV, churn, and conversion metrics
â   âââ budget_manager.py     # Tracks budget, MRR, phase progression, and spending
â   âââ social_research.py    # Scans Reddit, Twitter/X, HackerNews, ProductHunt
â   âââ heartbeat.py          # Monitors agent uptime, sends Discord/Telegram alerts
âââ .env.example              # All environment variables documented with comments
âââ .gitignore                # Excludes .env, state.json, and log files from version control
âââ LICENSE                   # MIT
âââ Makefile                  # make run, make logs, make state, make reset, make lint
âââ README.md                 # Public-facing project overview and quickstart
âââ agent_will.py             # Core agent â decision loop, action execution, state management
âââ config.py                 # All constants and environment variable loading
âââ requirements.txt          # All Python dependencies
âââ state.json                # Runtime state â persists across restarts, never committed
```

---

## Core Files

### `agent_will.py`
The brain. Contains the `AgentWill` class with four key methods:

| Method | Purpose |
|---|---|
| `load_state()` | Reads `state.json` on boot, restores Will's last known state |
| `save_state()` | Writes current state to `state.json` after every action |
| `_build_system_prompt()` | Constructs the LLM system prompt with phase, MRR, budget, niche, and research |
| `make_decision()` | Calls Claude API, parses JSON response, returns next action |
| `execute_action()` | Executes the chosen action, updates budget/MRR, queues next action |
| `run()` | Main loop â runs until TARGET_REVENUE is reached or agent halts |

### `config.py`
Single source of truth for all constants and environment variables. Everything `agent_will.py` needs is imported from here. All required API keys are validated on boot â Will raises `EnvironmentError` immediately if any required key is missing.

### `state.json`
Will's memory. Written after every action. Contains:
- `phase` â current business phase
- `current_objective_index` â which objective Will is working on
- `selected_niche` â the niche Will committed to after market research
- `last_research` â raw results from the last web and social search, injected into LLM prompts
- `action_queue` â pending actions to execute before calling LLM again
- `mrr_history` â last 5 MRR values, used for stuck detection
- `exit_prep_triggered` â manual flag to trigger Exit Prep phase
- `milestones` â timestamps of major revenue events

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
âââ tools/web_search.py         â WEB_SEARCH_API_KEY (Serper)
âââ tools/content_generator.py  â CONTENT_GENERATOR_API_KEY
âââ tools/data_analyzer.py      â no external API
âââ tools/budget_manager.py     â no external API
âââ tools/social_research.py    â WEB_SEARCH_API_KEY (Serper) + RAPIDAPI_KEY (optional)
âââ tools/heartbeat.py          â DISCORD_WEBHOOK_URL + TELEGRAM_BOT_TOKEN (both optional)
```

---

## The Decision Loop
```
âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
â                     run() â main loop                    â
â                                                         â
â  1. Is action_queue empty?                              â
â     YES â build context string â call make_decision()   â
â     NO  â skip LLM call, use queued action              â
â                 â                                       â
â  2. make_decision()                                     â
â     â check phase via check_budget_status()             â
â     â check if MRR >= TARGET_REVENUE                    â
â     â call _build_system_prompt()                       â
â     â call Claude API (claude-sonnet-4-6)               â
â     â parse JSON response                               â
â     â validate structure                                â
â     â return action dict                                â
â                 â                                       â
â  3. execute_action()                                    â
â     â look up phase_config from budget_manager         â
â     â execute chosen action (research, campaign, etc.) â
â     â update budget/MRR                                 â
â     â queue next logical action                         â
â     â return True (continue) or False (halt)            â
â                 â                                       â
â  4. save_state()                                        â
â     â write all state to state.json                     â
â                 â                                       â
â  5. Stuck detection                                     â
â     â if MRR unchanged for 5 consecutive actions        â
â     â halt with "Agent seems stuck" log entry           â
â                 â                                       â
â  6. sleep(0.5) â repeat                                 â
âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
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

## Research â Decision Feedback Loop
```
perform_market_research()
    â
    âââ web_search.execute()        â returns results dict
    âââ social_research.execute()   â returns results dict
    â
    âââ state['last_research'] = {
            'web': results,
            'social': social_results
        }
        save_state()
            â
            âââ next make_decision() call
                    â
                    âââ _build_system_prompt()
                            â
                            âââ injects web snippets + social result count
                                into system prompt
                                    â
                                    âââ LLM reasons about findings
                                        â calls select_niche with
                                          informed niche choice
```

---

## Phase Progression

| Phase | MRR Threshold | Key Behavior |
|---|---|---|
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
2. All previous state is restored â phase, objective, niche, research, action queue
3. If `action_queue` is non-empty, Will resumes mid-sequence without calling the LLM
4. If `action_queue` is empty, Will calls `make_decision()` with full context including previous research

Run `make reset` to wipe state and start Will from scratch.
# AgentWill Ã¢ÂÂ Architecture

> This document explains how every file in the AgentWill repo connects, how data flows through the system, and how Will makes autonomous decisions.

---

## Directory Structure
```
agentwill/
Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂ logs/
Ã¢ÂÂ   Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂ .gitkeep              # Keeps logs/ in version control without committing log files
Ã¢ÂÂ   Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂ agent_will.log        # Runtime log Ã¢ÂÂ every action Will takes, JSONL format
Ã¢ÂÂ   Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂ heartbeat.log         # Heartbeat monitor log Ã¢ÂÂ uptime checks
Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂ tools/
Ã¢ÂÂ   Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂ web_search.py         # Serper API wrapper Ã¢ÂÂ searches the web for market research
Ã¢ÂÂ   Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂ content_generator.py  # Generates marketing copy and slogans
Ã¢ÂÂ   Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂ data_analyzer.py      # Analyzes MRR, CAC, LTV, churn, and conversion metrics
Ã¢ÂÂ   Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂ budget_manager.py     # Tracks budget, MRR, phase progression, and spending
Ã¢ÂÂ   Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂ social_research.py    # Scans Reddit, Twitter/X, HackerNews, ProductHunt
Ã¢ÂÂ   Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂ heartbeat.py          # Monitors agent uptime, sends Discord/Telegram alerts
Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂ .env.example              # All environment variables documented with comments
Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂ .gitignore                # Excludes .env, state.json, and log files from version control
Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂ LICENSE                   # MIT
Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂ Makefile                  # make run, make logs, make state, make reset, make lint
Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂ README.md                 # Public-facing project overview and quickstart
Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂ agent_will.py             # Core agent Ã¢ÂÂ decision loop, action execution, state management
Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂ config.py                 # All constants and environment variable loading
Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂ requirements.txt          # All Python dependencies
Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂ state.json                # Runtime state Ã¢ÂÂ persists across restarts, never committed
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
| `run()` | Main loop Ã¢ÂÂ runs until TARGET_REVENUE is reached or agent halts |

### `config.py`
Single source of truth for all constants and environment variables. Everything `agent_will.py` needs is imported from here. All required API keys are validated on boot Ã¢ÂÂ Will raises `EnvironmentError` immediately if any required key is missing.

### `state.json`
Will's memory. Written after every action. Contains:
- `phase` Ã¢ÂÂ current business phase
- `current_objective_index` Ã¢ÂÂ which objective Will is working on
- `selected_niche` Ã¢ÂÂ the niche Will committed to after market research
- `last_research` Ã¢ÂÂ raw results from the last web and social search, injected into LLM prompts
- `action_queue` Ã¢ÂÂ pending actions to execute before calling LLM again
- `mrr_history` Ã¢ÂÂ last 5 MRR values, used for stuck detection
- `exit_prep_triggered` Ã¢ÂÂ manual flag to trigger Exit Prep phase
- `milestones` Ã¢ÂÂ timestamps of major revenue events

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
Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂ tools/web_search.py         Ã¢ÂÂ WEB_SEARCH_API_KEY (Serper)
Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂ tools/content_generator.py  Ã¢ÂÂ CONTENT_GENERATOR_API_KEY
Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂ tools/data_analyzer.py      Ã¢ÂÂ no external API
Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂ tools/budget_manager.py     Ã¢ÂÂ no external API
Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂ tools/social_research.py    Ã¢ÂÂ WEB_SEARCH_API_KEY (Serper) + RAPIDAPI_KEY (optional)
Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂ tools/heartbeat.py          Ã¢ÂÂ DISCORD_WEBHOOK_URL + TELEGRAM_BOT_TOKEN (both optional)
```

---

## The Decision Loop
```
Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
Ã¢ÂÂ                     run() Ã¢ÂÂ main loop                    Ã¢ÂÂ
Ã¢ÂÂ                                                         Ã¢ÂÂ
Ã¢ÂÂ  1. Is action_queue empty?                              Ã¢ÂÂ
Ã¢ÂÂ     YES Ã¢ÂÂ build context string Ã¢ÂÂ call make_decision()   Ã¢ÂÂ
Ã¢ÂÂ     NO  Ã¢ÂÂ skip LLM call, use queued action              Ã¢ÂÂ
Ã¢ÂÂ                 Ã¢ÂÂ                                       Ã¢ÂÂ
Ã¢ÂÂ  2. make_decision()                                     Ã¢ÂÂ
Ã¢ÂÂ     Ã¢ÂÂ check phase via check_budget_status()             Ã¢ÂÂ
Ã¢ÂÂ     Ã¢ÂÂ check if MRR >= TARGET_REVENUE                    Ã¢ÂÂ
Ã¢ÂÂ     Ã¢ÂÂ call _build_system_prompt()                       Ã¢ÂÂ
Ã¢ÂÂ     Ã¢ÂÂ call Claude API (claude-sonnet-4-6)               Ã¢ÂÂ
Ã¢ÂÂ     Ã¢ÂÂ parse JSON response                               Ã¢ÂÂ
Ã¢ÂÂ     Ã¢ÂÂ validate structure                                Ã¢ÂÂ
Ã¢ÂÂ     Ã¢ÂÂ return action dict                                Ã¢ÂÂ
Ã¢ÂÂ                 Ã¢ÂÂ                                       Ã¢ÂÂ
Ã¢ÂÂ  3. execute_action()                                    Ã¢ÂÂ
Ã¢ÂÂ     Ã¢ÂÂ look up phase_config from budget_manager         Ã¢ÂÂ
Ã¢ÂÂ     Ã¢ÂÂ execute chosen action (research, campaign, etc.) Ã¢ÂÂ
Ã¢ÂÂ     Ã¢ÂÂ update budget/MRR                                 Ã¢ÂÂ
Ã¢ÂÂ     Ã¢ÂÂ queue next logical action                         Ã¢ÂÂ
Ã¢ÂÂ     Ã¢ÂÂ return True (continue) or False (halt)            Ã¢ÂÂ
Ã¢ÂÂ                 Ã¢ÂÂ                                       Ã¢ÂÂ
Ã¢ÂÂ  4. save_state()                                        Ã¢ÂÂ
Ã¢ÂÂ     Ã¢ÂÂ write all state to state.json                     Ã¢ÂÂ
Ã¢ÂÂ                 Ã¢ÂÂ                                       Ã¢ÂÂ
Ã¢ÂÂ  5. Stuck detection                                     Ã¢ÂÂ
Ã¢ÂÂ     Ã¢ÂÂ if MRR unchanged for 5 consecutive actions        Ã¢ÂÂ
Ã¢ÂÂ     Ã¢ÂÂ halt with "Agent seems stuck" log entry           Ã¢ÂÂ
Ã¢ÂÂ                 Ã¢ÂÂ                                       Ã¢ÂÂ
Ã¢ÂÂ  6. sleep(0.5) Ã¢ÂÂ repeat                                 Ã¢ÂÂ
Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
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

## Research Ã¢ÂÂ Decision Feedback Loop
```
perform_market_research()
    Ã¢ÂÂ
    Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂ web_search.execute()        Ã¢ÂÂ returns results dict
    Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂ social_research.execute()   Ã¢ÂÂ returns results dict
    Ã¢ÂÂ
    Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂ state['last_research'] = {
            'web': results,
            'social': social_results
        }
        save_state()
            Ã¢ÂÂ
            Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂ next make_decision() call
                    Ã¢ÂÂ
                    Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂ _build_system_prompt()
                            Ã¢ÂÂ
                            Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂ injects web snippets + social result count
                                into system prompt
                                    Ã¢ÂÂ
                                    Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂ LLM reasons about findings
                                        Ã¢ÂÂ calls select_niche with
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
2. All previous state is restored Ã¢ÂÂ phase, objective, niche, research, action queue
3. If `action_queue` is non-empty, Will resumes mid-sequence without calling the LLM
4. If `action_queue` is empty, Will calls `make_decision()` with full context including previous research

Run `make reset` to wipe state and start Will from scratch.
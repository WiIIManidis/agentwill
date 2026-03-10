# AgentWill -- Phases

> This document covers all 7 business phases Will progresses through on the way to $50,000/month MRR, what triggers each phase, how Will's behavior changes, and how Exit Prep works differently from all other phases.

---

## Overview

Will operates in phases. Each phase represents a stage of business maturity and unlocks a different cost configuration -- campaign costs, MVP development costs, growth factors, and success probabilities all scale with phase. Phase is determined automatically by current MRR, with one exception: Exit Prep is triggered manually.

```
$0          $100        $1,000      $10,000     $25,000     $50,000
|           |           |           |           |           |
Seed -----> Pre-Seed -> Series A -> Series B -> Series C -> IPO -> Exit Prep
                                                                        ^
                                                               Manual trigger only
```

---

## Phase Breakdown

---

### Phase 1 -- Seed
**MRR Threshold:** $0+
**Objective:** Identify a viable market niche

This is where Will starts. Budget is limited, costs are low, and the focus is entirely on market research and niche selection. Will scans the web and social platforms for pain points, scores niche candidates, and commits to one via `select_niche`.

**Key behaviors:**
- `perform_market_research` is the dominant action
- `select_niche` is called once research results are injected into the system prompt
- Low `market_research_cost` -- Will can run many searches before moving on
- `move_to_next_objective` fires after niche is selected

**What changes at $100 MRR:** Will transitions to Pre-Seed automatically

---

### Phase 2 -- Pre-Seed
**MRR Threshold:** $100+
**Objective:** Develop an MVP

Will has identified a niche and now builds the minimum viable product. MVP development cost is deducted from budget. Content generation becomes available -- Will starts producing marketing copy for the product before it launches.

**Key behaviors:**
- `design_and_build_mvp` is the primary action
- `generate_marketing_content` becomes active -- slogans and copy are generated using the selected niche
- `mvp_development_cost` is deducted on successful MVP build
- `move_to_next_objective` fires after MVP is complete

**What changes at $1,000 MRR:** Will transitions to Series A automatically

---

### Phase 3 -- Series A
**MRR Threshold:** $1,000+
**Objective:** Acquire first paying customers

Will has an MVP and starts running marketing campaigns to acquire customers. Campaign success probability increases from the Seed phase. Will alternates between launching campaigns, analyzing performance, and generating new content based on what the data recommends.

**Key behaviors:**
- `launch_marketing_campaign` is the dominant action
- `analyze_performance` fires regularly -- Will checks CAC, LTV, churn, and conversion rate
- `generate_marketing_content` fires when `data_analyzer` recommends A/B testing
- Campaign success probability is moderate -- some campaigns succeed, some partially succeed
- MRR grows via `base_mrr_gain` + `mrr_growth_factor` on successful campaigns

**What changes at $10,000 MRR:** Will transitions to Series B automatically

---

### Phase 4 -- Series B
**MRR Threshold:** $10,000+
**Objective:** Scale revenue to $50,000/month

Will shifts from acquisition to optimization. Campaign costs increase but growth factors also increase -- each successful campaign generates more MRR. `optimize_and_scale` becomes available and is more effective than raw campaign spend at this stage.

**Key behaviors:**
- `optimize_and_scale` becomes the dominant action alongside campaigns
- Higher `mrr_growth_factor` -- campaigns generate more MRR per run
- Higher `campaign_success_probability` -- Will is better at marketing now
- `analyze_performance` drives decisions -- Will listens to the data closely
- `evaluate_current_strategy` -> `analyze_performance` loop fires regularly

**What changes at $25,000 MRR:** Will transitions to Series C automatically

---

### Phase 5 -- Series C
**MRR Threshold:** $25,000+
**Objective:** Scale revenue to $50,000/month

Aggressive scaling. Will is running at near-full efficiency -- high campaign success rates, high growth factors, and optimization costs that generate outsized MRR returns. The focus is pure execution toward the $50K target.

**Key behaviors:**
- `optimize_and_scale` and `launch_marketing_campaign` alternate rapidly
- Very high `campaign_success_probability`
- High `mrr_growth_factor_scale` -- scaling actions generate significant MRR jumps
- `analyze_performance` still fires but recommendations are mostly "keep scaling"
- Stuck detection becomes more important -- if MRR plateaus here, Will halts

**What changes at $50,000 MRR:** Will transitions to IPO automatically

---

### Phase 6 -- IPO
**MRR Threshold:** $50,000+
**Objective:** Revenue consolidation

Will has hit the target. IPO phase is revenue consolidation -- Will continues optimizing and scaling to maintain and grow MRR, preparing the business for maximum valuation before exit. Campaign costs are high but ROI is highest here.

**Key behaviors:**
- `optimize_and_scale` is the primary action
- `mission_accomplished` fires -- Will logs the achievement
- MRR is at or above $50,000
- Business is stable and generating consistent revenue
- Exit Prep can be triggered manually at this stage

**What triggers Exit Prep:** Manual flag only -- see below

---

### Phase 7 -- Exit Prep
**MRR Threshold:** Manual trigger only
**Objective:** List and sell the business

Exit Prep is different from all other phases. It is never triggered automatically by MRR -- it is triggered by setting `exit_prep_triggered: true` in `state.json` manually. This is intentional: Will should not decide to sell the business autonomously.

**How to trigger:**
```bash
# Edit state.json directly
"exit_prep_triggered": true

# Or use a future make command:
make exit
```

**Key behaviors:**
- `legal_broker_cost` replaces `campaign_cost` -- Will is paying for legal and brokerage fees
- `mvp_development_cost` is $0 -- no new product development
- Will focuses on business listing preparation
- Target platforms: Acquire.com, MicroAcquire, Flippa
- `milestones['business_listed']` is timestamped when listing goes live
- `milestones['business_sold']` is timestamped on sale
- `exit_multiple` and `sale_price` are recorded in `state.json`

---

## Phase Configuration Reference

Each phase has its own cost and growth configuration in `budget_manager.py`. Here is what each field controls:

| Field | Description |
|---|---|
| `market_research_cost` | Cost per web + social research run |
| `mvp_development_cost` | One-time cost to build MVP |
| `content_generation_cost` | Cost per marketing content generation run |
| `campaign_cost` | Cost per marketing campaign launch |
| `optimization_cost` | Cost per optimize_and_scale run |
| `mrr_growth_factor` | MRR multiplier on successful campaign |
| `mrr_growth_factor_scale` | MRR multiplier on optimize_and_scale |
| `base_mrr_gain` | Flat MRR added on successful campaign |
| `base_mrr_gain_scale` | Flat MRR added on optimize_and_scale |
| `campaign_success_probability` | Probability a campaign fully succeeds (0.0-1.0) |
| `visitor_traffic_base` | Base simulated visitor traffic for data_analyzer |
| `visitor_traffic_mrr_factor` | Traffic scaling factor based on MRR |
| `conversion_rate_base` | Base conversion rate for data_analyzer |
| `conversion_rate_growth` | Conversion rate improvement factor |
| `churn_rate_base` | Base churn rate for data_analyzer |
| `churn_rate_reduction` | Churn improvement factor |
| `cac_base` | Base customer acquisition cost |
| `cac_reduction` | CAC improvement factor |
| `ltv_growth_factor` | LTV improvement factor |

---

## Phase Transition Rules

- Phases Seed through IPO transition **automatically** when MRR crosses the threshold
- Phase is checked at the start of every `make_decision()` call via `check_budget_status()`
- Phase is also checked at the start of every `execute_action()` call -- Will always uses the correct phase config
- Will cannot move backwards through phases -- once a threshold is crossed it stays crossed
- Exit Prep **never** transitions automatically -- it requires `exit_prep_triggered: true` in `state.json`

---

## Checking Will's Current Phase

```bash
# Print current state including phase
make state

# Or read the log for phase transition entries
make logs
```

Phase transition log entries look like:
```json
{
  "timestamp": "2026-03-08T14:22:01.441Z",
  "phase": "Series A",
  "action": "Moving to next objective: Acquire first paying customers",
  "current_mrr": 1024.50,
  "outcome": "Success"
}
```

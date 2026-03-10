import json
import time
import os
import random
from datetime import datetime
from collections import deque
from anthropic import Anthropic
from config import AGENT_NAME, INITIAL_BUDGET, ETHICAL_GUIDELINES, LOG_FILE, STATE_FILE, TARGET_REVENUE, OPENCLAW_MODEL
from tools.web_search import WebSearchTool
from tools.content_generator import ContentGeneratorTool
from tools.data_analyzer import DataAnalyzerTool
from tools.budget_manager import BudgetManager
from tools.social_research import SocialResearchTool

# Ensure logs directory exists
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)


class AgentWill:
    def __init__(self):
        self.name = AGENT_NAME
        self.client = Anthropic()
        self.budget_manager = BudgetManager(initial_budget=INITIAL_BUDGET)
        self.tools = {
            "web_search": WebSearchTool(),
            "content_generator": ContentGeneratorTool(),
            "data_analyzer": DataAnalyzerTool(),
            "budget_manager": self.budget_manager,
            "social_research": SocialResearchTool()
        }
        self.state = self.load_state()
        self.phase = self.state.get('phase', "Initialization")
        self.objectives = [
            "Identify a viable market niche",
            "Develop an MVP",
            "Acquire first paying customers",
            "Scale revenue to $50,000/month"
        ]
        self.current_objective_index = self.state.get('current_objective_index', 0)
        self.action_queue = deque(self.state.get('action_queue', []))
        self.mrr_history = deque(self.state.get('mrr_history', []), maxlen=5)
        self.log_action(f"Agent {self.name} initialized with budget ${self.budget_manager.current_budget:.2f}")

    def load_state(self):
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        return {
            'phase': "Initialization",
            'current_objective_index': 0,
            'action_queue': [],
            'mrr_history': [],
            'exit_prep_triggered': False,
            'selected_niche': None,
            'last_research': {}
        }

    def save_state(self):
        self.state['phase'] = self.phase
        self.state['current_objective_index'] = self.current_objective_index
        self.state['action_queue'] = list(self.action_queue)
        self.state['mrr_history'] = list(self.mrr_history)
        with open(STATE_FILE, 'w') as f:
            json.dump(self.state, f, indent=4)

    def log_action(self, action_description, tool_used=None, cost=0.0, revenue_impact=0.0, outcome="Success"):
        timestamp = datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "phase": self.phase,
            "current_objective": self.objectives[self.current_objective_index],
            "action": action_description,
            "tool_used": tool_used,
            "cost": cost,
            "revenue_impact": revenue_impact,
            "outcome": outcome,
            "current_mrr": self.budget_manager.mrr,
            "current_budget": self.budget_manager.current_budget
        }
        with open(LOG_FILE, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
        print(f"[{timestamp}] {self.name} ({self.phase}): {action_description} [MRR: ${self.budget_manager.mrr:.2f}, Budget: ${self.budget_manager.current_budget:.2f}]")

    def _build_system_prompt(self):
        """
        Builds the full system prompt for the LLM decision call.
        Injects current state, phase, research findings, and ethical constraints.
        """
        last_research = self.state.get('last_research', {})
        research_summary = ""
        if last_research:
            web = last_research.get('web', {})
            social = last_research.get('social', {})
            web_snippets = " | ".join([r.get('snippet', '')[:100] for r in web.get('results', [])[:3]])
            research_summary = f"""
Last research findings:
- Web results: {web.get('num_results_returned', 0)} results for query: "{web.get('query', 'N/A')}"
- Web snippets: {web_snippets}
- Social results: {social.get('total_results', 0)} total results across Reddit, Twitter/X, HackerNews, ProductHunt
- If niche not yet selected, use select_niche action with your best niche choice based on these findings.
"""

        selected_niche = self.state.get('selected_niche', 'Not yet identified')

        return f"""You are {self.name}, a fully autonomous AI business agent running on a Mac Mini.
Your sole objective is to reach ${TARGET_REVENUE:,.0f}/month in MRR starting from $0, completely autonomously.

Current State:
- Phase: {self.phase}
- MRR: ${self.budget_manager.mrr:.2f}
- Budget: ${self.budget_manager.current_budget:.2f}
- Current Objective: {self.objectives[self.current_objective_index]}
- Selected Niche: {selected_niche}
{research_summary}
Available agent actions:
- perform_market_research: Search web and social platforms for market trends and pain points
- select_niche: Commit to a specific business niche based on research findings -- use this after perform_market_research
- design_and_build_mvp: Design and build the MVP for the selected niche
- launch_marketing_campaign: Launch a marketing campaign to acquire customers
- optimize_and_scale: Optimize operations and scale revenue
- analyze_performance: Analyze current performance data and metrics
- evaluate_current_strategy: Evaluate and reassess current strategy
- generate_marketing_content: Generate marketing copy and content
- move_to_next_objective: Advance to the next business objective

You must respond with ONLY a valid JSON object in this exact format, no preamble, no explanation:
{{"tool": "agent_action", "tool_input": {{"action_name": "action_name_here"}}}}

For select_niche, use this format:
{{"tool": "agent_action", "tool_input": {{"action_name": "select_niche", "niche": "your chosen niche here"}}}}

Ethical constraints you must always follow:
{chr(10).join(f"- {g}" for g in ETHICAL_GUIDELINES)}"""

    def make_decision(self, context):
        """
        Real OpenClaw LLM-driven decision making using Claude.
        Replaces the previous if/elif keyword matching placeholder.
        """
        self.log_action(f"Analyzing context for decision: {context}")

        # Update phase before deciding
        budget_status = self.budget_manager.check_budget_status(
            self.budget_manager.mrr,
            exit_prep_triggered=self.state.get('exit_prep_triggered', False)
        )
        self.phase = budget_status['current_mrr_phase']

        # Check mission accomplished before calling LLM
        if self.budget_manager.mrr >= TARGET_REVENUE:
            return {"tool": "agent_action", "tool_input": {"action_name": "mission_accomplished"}}

        try:
            response = self.client.messages.create(
                model=OPENCLAW_MODEL,
                max_tokens=256,
                system=self._build_system_prompt(),
                messages=[{"role": "user", "content": context}]
            )

            raw = response.content[0].text.strip()
            self.log_action(f"LLM raw response: {raw}")

            # Strip markdown code fences if present
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
                raw = raw.strip()

            decision = json.loads(raw)

            # Validate decision structure
            if "tool" not in decision or "tool_input" not in decision:
                raise ValueError(f"Invalid decision structure: {decision}")

            self.log_action(f"LLM decision: {decision.get('tool_input', {}).get('action_name', 'unknown')}")
            return decision

        except json.JSONDecodeError as e:
            self.log_action(f"LLM JSON parse failed: {e}. Raw: {raw}", outcome="Warning")
            return {"tool": "agent_action", "tool_input": {"action_name": "evaluate_current_strategy"}}
        except Exception as e:
            self.log_action(f"LLM decision call failed: {e}", outcome="Error")
            return {"tool": "agent_action", "tool_input": {"action_name": "evaluate_current_strategy"}}

    def execute_action(self, action_dict):
        action_type = action_dict.get("tool")
        action_input = action_dict.get("tool_input", {})

        if action_type == "agent_action":
            action = action_input.get("action_name")

            # Get current phase configuration
            budget_status = self.budget_manager.check_budget_status(
                self.budget_manager.mrr,
                exit_prep_triggered=self.state.get('exit_prep_triggered', False)
            )
            phase_config = budget_status['phase_config']

            if action == "perform_market_research":
                cost = phase_config['market_research_cost']
                deduct_response = self.budget_manager.deduct_funds(cost, description="Market Research", mrr=self.budget_manager.mrr)
                if deduct_response["status"] == "success":
                    results = self.tools["web_search"].execute(
                        query="market trends, unmet needs, competitor analysis",
                        search_type='general',
                        niche=self.state.get('selected_niche')
                    )
                    social_results = self.tools['social_research'].execute(
                        query='market trends, unmet needs, competitor analysis',
                        platform='all',
                        niche=self.state.get('selected_niche')
                    )

                    # Save research to state for LLM context injection
                    self.state['last_research'] = {
                        'web': results,
                        'social': social_results
                    }
                    self.save_state()

                    total_social = social_results.get('total_results', social_results.get('num_results_returned', 0))
                    self.log_action(
                        "Performed market research",
                        "web_search + social_research",
                        cost=cost,
                        outcome=f"Found {results['num_results_returned']} web results and {total_social} social results. Status: {results['status']}"
                    )
                    if self.current_objective_index == 0:
                        self.log_action("Market research completed, ready to define MVP.", outcome="Success")
                        self.action_queue.appendleft({"tool": "agent_action", "tool_input": {"action_name": "move_to_next_objective"}})
                    return True
                else:
                    self.log_action("Attempted market research", tool_used="web_search", cost=cost, outcome=f"Failed: {deduct_response['message']}")
                    self.action_queue.appendleft({"tool": "agent_action", "tool_input": {"action_name": "evaluate_current_strategy"}})
                    return True

            elif action == "select_niche":
                niche = action_input.get("niche", "Not specified")
                self.state['selected_niche'] = niche
                self.save_state()
                self.log_action(
                    f"Niche selected: {niche}",
                    outcome="Success -- niche committed to state.json"
                )
                self.action_queue.appendleft({"tool": "agent_action", "tool_input": {"action_name": "move_to_next_objective"}})
                return True

            elif action == "design_and_build_mvp":
                cost = phase_config['mvp_development_cost']
                deduct_response = self.budget_manager.deduct_funds(cost, description="MVP Development", mrr=self.budget_manager.mrr)
                if deduct_response["status"] == "success":
                    self.log_action("Designed and built MVP", cost=cost, outcome="MVP ready for launch.")
                    self.action_queue.appendleft({"tool": "agent_action", "tool_input": {"action_name": "move_to_next_objective"}})
                    return True
                else:
                    self.log_action("Attempted MVP development", cost=cost, outcome=f"Failed: {deduct_response['message']}")
                    self.action_queue.appendleft({"tool": "agent_action", "tool_input": {"action_name": "evaluate_current_strategy"}})
                    return True

            elif action == "generate_marketing_content":
                cost = phase_config['content_generation_cost']
                deduct_response = self.budget_manager.deduct_funds(cost, description="Content Generation", mrr=self.budget_manager.mrr)
                if deduct_response["status"] == "success":
                    content_gen_output = self.tools["content_generator"].execute(
                        content_type="marketing_slogan",
                        prompt=f"short marketing slogan for {self.state.get('selected_niche', 'a new SaaS product')}",
                        mrr_phase=self.phase
                    )
                    generated_content = f"Slogan: {content_gen_output['generation_prompt'][:50]}..."
                    self.log_action("Generated marketing content", "content_generator", cost=cost, outcome=f"Content: {generated_content}")
                    return True
                else:
                    self.log_action("Attempted content generation", tool_used="content_generator", cost=cost, outcome=f"Failed: {deduct_response['message']}")
                    self.action_queue.appendleft({"tool": "agent_action", "tool_input": {"action_name": "evaluate_current_strategy"}})
                    return True

            elif action == "analyze_performance":
                current_mrr = self.budget_manager.mrr

                visitor_traffic = phase_config['visitor_traffic_base'] + int(current_mrr * phase_config['visitor_traffic_mrr_factor'])
                conversion_rate_sim = phase_config['conversion_rate_base'] + (current_mrr / TARGET_REVENUE * phase_config['conversion_rate_growth'])
                churn_rate_sim = phase_config['churn_rate_base'] - (current_mrr / TARGET_REVENUE * phase_config['churn_rate_reduction'])
                cac_sim = phase_config['cac_base'] - (current_mrr / TARGET_REVENUE * phase_config['cac_reduction'])
                ltv_sim = cac_sim * (1.0 + (current_mrr / TARGET_REVENUE * phase_config['ltv_growth_factor']))

                data = {
                    "mrr": current_mrr,
                    "revenue": current_mrr * 1.1,
                    "churn_rate": max(0.01, churn_rate_sim),
                    "cac": max(10.0, cac_sim),
                    "ltv": max(50.0, ltv_sim),
                    "conversion_rate": min(0.05, conversion_rate_sim),
                    "visitor_traffic": visitor_traffic
                }
                analysis_result = self.tools["data_analyzer"].analyze(data)
                self.log_action(
                    "Analyzed performance data",
                    "data_analyzer",
                    outcome=f"Analysis: {analysis_result['current_phase']} - {analysis_result['recommendations'][0] if analysis_result['recommendations'] else 'No specific recommendation.'}"
                )

                self.phase = analysis_result['current_phase']
                if analysis_result['phase_progression'] == 'advance':
                    self.log_action(f"Data analysis suggests to advance phase: {analysis_result['recommendations'][0]}")
                    self.action_queue.appendleft({"tool": "agent_action", "tool_input": {"action_name": "move_to_next_objective"}})
                elif "Prioritize A/B testing" in (analysis_result['recommendations'][0] if analysis_result['recommendations'] else '') and self.current_objective_index > 1:
                    self.action_queue.appendleft({"tool": "agent_action", "tool_input": {"action_name": "generate_marketing_content"}})
                elif "Review customer acquisition" in (analysis_result['recommendations'][0] if analysis_result['recommendations'] else '') and self.current_objective_index > 1:
                    self.action_queue.appendleft({"tool": "agent_action", "tool_input": {"action_name": "launch_marketing_campaign"}})
                return True

            elif action == "launch_marketing_campaign":
                current_mrr = self.budget_manager.mrr
                cost = phase_config['campaign_cost']

                deduct_response = self.budget_manager.deduct_funds(cost, description="Marketing Campaign", mrr=current_mrr)
                if deduct_response["status"] == "success":
                    self.log_action("Launched marketing campaign", cost=cost)

                    mrr_gain_factor = phase_config['mrr_growth_factor']
                    campaign_success_prob = phase_config['campaign_success_probability']

                    if random.random() < campaign_success_prob:
                        add_mrr_impact = current_mrr * mrr_gain_factor + phase_config['base_mrr_gain']
                        self.budget_manager.add_funds(add_mrr_impact * 2, description="Revenue from campaign (simulated)", mrr_impact=add_mrr_impact)
                        self.log_action("Generated revenue from marketing", revenue_impact=add_mrr_impact * 2, outcome=f"New MRR: ${self.budget_manager.mrr:.2f}")
                    else:
                        add_mrr_impact = phase_config['base_mrr_gain'] * 0.1
                        self.budget_manager.add_funds(add_mrr_impact * 2, description="Revenue from campaign (simulated - partial success)", mrr_impact=add_mrr_impact)
                        self.log_action("Marketing campaign had limited success", revenue_impact=add_mrr_impact * 2, outcome=f"MRR increased by ${add_mrr_impact:.2f}")

                    self.action_queue.appendleft({"tool": "agent_action", "tool_input": {"action_name": "evaluate_current_strategy"}})
                    return True
                else:
                    self.log_action("Attempted marketing campaign", cost=cost, outcome=f"Failed: {deduct_response['message']}")
                    self.action_queue.appendleft({"tool": "agent_action", "tool_input": {"action_name": "evaluate_current_strategy"}})
                    return True

            elif action == "optimize_and_scale":
                current_mrr = self.budget_manager.mrr
                cost = phase_config['optimization_cost']

                deduct_response = self.budget_manager.deduct_funds(cost, description="Optimization & Scaling", mrr=current_mrr)
                if deduct_response["status"] == "success":
                    self.log_action("Optimizing operations for scaling", cost=cost)

                    mrr_gain_factor = phase_config['mrr_growth_factor_scale']
                    add_mrr_impact = current_mrr * mrr_gain_factor + phase_config['base_mrr_gain_scale']

                    self.budget_manager.add_funds(add_mrr_impact * 2, description="Revenue from scaling (simulated)", mrr_impact=add_mrr_impact)
                    self.log_action("Scaled operations and generated more revenue", revenue_impact=add_mrr_impact * 2, outcome=f"MRR increased by ${add_mrr_impact:.2f}")

                    if self.budget_manager.mrr >= TARGET_REVENUE:
                        self.action_queue.appendleft({"tool": "agent_action", "tool_input": {"action_name": "mission_accomplished"}})
                    else:
                        self.action_queue.appendleft({"tool": "agent_action", "tool_input": {"action_name": "evaluate_current_strategy"}})
                    return True
                else:
                    self.log_action("Attempted optimization and scaling", cost=cost, outcome=f"Failed: {deduct_response['message']}")
                    self.action_queue.appendleft({"tool": "agent_action", "tool_input": {"action_name": "evaluate_current_strategy"}})
                    return True

            elif action == "mission_accomplished":
                self.log_action(f"{self.name} has achieved its goal: ${TARGET_REVENUE:,.2f} MRR!")
                return False

            elif action == "evaluate_current_strategy":
                self.log_action("Evaluating current strategy and progress...")
                self.action_queue.appendleft({"tool": "agent_action", "tool_input": {"action_name": "analyze_performance"}})
                return True

            elif action == "move_to_next_objective":
                if self.current_objective_index < len(self.objectives) - 1:
                    self.current_objective_index += 1
                    self.log_action(f"Moving to next objective: {self.objectives[self.current_objective_index]}")
                    return True
                else:
                    self.action_queue.appendleft({"tool": "agent_action", "tool_input": {"action_name": "mission_accomplished"}})
                    return True

        return True

    def run(self):
        self.log_action(f"{self.name} starting its autonomous operation.")
        executable = True
        while executable and self.budget_manager.mrr < TARGET_REVENUE:
            if not self.action_queue:
                current_objective = self.objectives[self.current_objective_index]

                budget_status_response = self.budget_manager.check_budget_status(
                    self.budget_manager.mrr,
                    exit_prep_triggered=self.state.get('exit_prep_triggered', False)
                )
                self.phase = budget_status_response['current_mrr_phase']
                current_budget = budget_status_response['current_balance']

                context = (
                    f"Current objective: {current_objective}. "
                    f"Current MRR: ${self.budget_manager.mrr:.2f}. "
                    f"Budget: ${current_budget:.2f}. "
                    f"Phase: {self.phase}. "
                    f"Selected niche: {self.state.get('selected_niche', 'Not yet identified')}. "
                    f"What is the single best action to take right now to make progress toward the current objective?"
                )

                action_to_take = self.make_decision(context)
                self.action_queue.append(action_to_take)

            action_to_execute = self.action_queue.popleft()

            if action_to_execute.get("tool_input", {}).get("action_name") == "mission_accomplished":
                executable = False
                continue

            self.mrr_history.append(self.budget_manager.mrr)

            executable = self.execute_action(action_to_execute)
            self.save_state()

            if not executable:
                break

            if self.current_objective_index >= 2 and \
               len(self.mrr_history) == self.mrr_history.maxlen and \
               all(mrr == self.mrr_history[0] for mrr in self.mrr_history):
                self.log_action("Agent seems stuck: MRR has not changed for 5 consecutive actions.", outcome="Halted")
                executable = False

            time.sleep(0.5)

        if self.budget_manager.mrr >= TARGET_REVENUE:
            self.log_action("Target MRR achieved! AgentWill operation concluded.")
        else:
            self.log_action("AgentWill stopped before reaching target, possibly due to budget constraints, logic loop, or early termination.")


if __name__ == "__main__":
    agent = AgentWill()
    agent.run()

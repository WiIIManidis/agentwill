import json
import time
import os
from datetime import datetime
from config import AGENT_NAME, INITIAL_BUDGET, ETHICAL_GUIDELINES, LOG_FILE
from tools.web_search import WebSearchTool
from tools.content_generator import ContentGeneratorTool
from tools.data_analyzer import DataAnalyzerTool
from tools.budget_manager import BudgetManager

# Ensure logs directory exists
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

class AgentWill:
    def __init__(self):
        self.name = AGENT_NAME
        self.budget_manager = BudgetManager(initial_budget=INITIAL_BUDGET)
        self.tools = {
            "web_search": WebSearchTool(),
            "content_generator": ContentGeneratorTool(),
            "data_analyzer": DataAnalyzerTool(),
            "budget_manager": self.budget_manager # Add budget_manager instance to tools
        }
        self.revenue = 0.0 # This should ideally be synchronized or derived from MRR in budget_manager or data_analyzer
        self.mrr = 0.0 # Monthly Recurring Revenue
        self.phase = "Initialization"
        self.objectives = [
            "Identify a viable market niche",
            "Develop an MVP",
            "Acquire first paying customers",
            "Scale revenue to $50,000/month"
        ]
        self.current_objective_index = 0
        self.log_action(f"Agent {self.name} initialized with budget ${self.budget_manager.current_budget:.2f}")

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
            "current_revenue": self.revenue, # This might become redundant if MRR is primary metric
            "current_mrr": self.mrr,
            "current_budget": self.budget_manager.current_budget
        }
        with open(LOG_FILE, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
        print(f"[{timestamp}] {self.name} ({self.phase}): {action_description} [MRR: ${self.mrr:.2f}, Budget: ${self.budget_manager.current_budget:.2f}]")

    def make_decision(self, context):
        # A placeholder for advanced LLM-driven decision making
        # In a real OpenClaw agent, this would involve complex reasoning
        # using an LLM to choose the best action based on context, objectives, and tool capabilities.
        self.log_action(f"Analyzing context for decision: {context}")

        # Update phase based on MRR before making decisions
        budget_status = self.budget_manager.check_budget_status(self.mrr)
        self.phase = budget_status['current_mrr_phase']

        if "market research" in context.lower() and self.current_objective_index == 0:
            return "perform_market_research"
        elif "create content" in context.lower():
            return "generate_marketing_content"
        elif "analyze data" in context.lower():
            return "analyze_performance"
        elif self.mrr >= 50000.0 and self.current_objective_index == len(self.objectives) - 1:
            return "mission_accomplished"
        elif "next objective" in context.lower() or "move to next phase" in context.lower():
            if self.current_objective_index < len(self.objectives) - 1:
                self.current_objective_index += 1
                # Phase will be updated by check_budget_status in the next loop iteration
                self.log_action(f"Moving to next objective: {self.objectives[self.current_objective_index]}")
                return self.objective_to_action(self.objectives[self.current_objective_index])
            else:
                return "mission_accomplished"
        else:
            # Default action based on current objective if no specific trigger
            return self.objective_to_action(self.objectives[self.current_objective_index])

    def objective_to_action(self, objective):
        if "market niche" in objective:
            return "perform_market_research"
        elif "MVP" in objective:
            return "design_and_build_mvp" # Placeholder for complex build tasks
        elif "paying customers" in objective:
            return "launch_marketing_campaign"
        elif "$50,000" in objective:
            return "optimize_and_scale"
        return "evaluate_current_strategy"

    def execute_action(self, action, *args, **kwargs):
        if action == "perform_market_research":
            cost = 10.0 # Simulate API cost
            deduct_response = self.budget_manager.deduct_funds(cost, description="Market Research", mrr=self.mrr)
            if deduct_response["status"] == "success":
                results = self.tools["web_search"].search("market trends, unmet needs, competitor analysis")
                self.log_action("Performed market research", "web_search", cost=cost, outcome=f"Found {len(results)} search results.")
                if self.current_objective_index == 0:
                    self.log_action("Market research completed, ready to define MVP.", outcome="Success")
                    return self.make_decision("move to next phase")
            else:
                self.log_action("Attempted market research", tool_used="web_search", cost=cost, outcome=f"Failed: {deduct_response['message']}")

        elif action == "design_and_build_mvp":
            cost = 100.0 # Simulate MVP development cost
            deduct_response = self.budget_manager.deduct_funds(cost, description="MVP Development", mrr=self.mrr)
            if deduct_response["status"] == "success":
                self.log_action("Designed and built MVP", cost=cost, outcome="MVP ready for launch.")
                return self.make_decision("move to next phase")
            else:
                self.log_action("Attempted MVP development", cost=cost, outcome=f"Failed: {deduct_response['message']}")

        elif action == "generate_marketing_content":
            cost = 5.0 # Simulate content generation cost
            deduct_response = self.budget_manager.deduct_funds(cost, description="Content Generation", mrr=self.mrr)
            if deduct_response["status"] == "success":
                # Placeholder for actual content generation using the content_generator tool's workflow
                # For now, simulate directly generating without agent LLM interaction for brevity in agent_will.py
                content_gen_output = self.tools["content_generator"].execute(
                    content_type="marketing_slogan", 
                    prompt="short marketing slogan for a new SaaS product", 
                    mrr_phase=self.phase.split(':')[0].lower().replace(' ', '_') # Extract phase like 'phase 1' -> 'phase_1'
                )
                # Assume for simplicity that agent immediately uses the generation_prompt with its LLM
                # and gets content. Then passes for validation. This is a simplification.
                generated_content = f"Slogan: {content_gen_output['generation_prompt'][:50]}..."
                self.log_action("Generated marketing content", "content_generator", cost=cost, outcome=f"Content: {generated_content}")
            else:
                self.log_action("Attempted content generation", tool_used="content_generator", cost=cost, outcome=f"Failed: {deduct_response['message']}")

        elif action == "analyze_performance":
            # Simulate getting data from a 'live' MVP or marketing campaign
            # Adjust dummy data to be more dynamic and reflect MRR
            # Assuming basic conversion for initial revenues
            visitor_traffic = 100 + int(self.mrr * 10)
            conversion_rate_sim = 0.01 + (self.mrr / 50000 * 0.04) # Increases with MRR
            revenue_sim = self.mrr * 1.1 # Simulate total revenue slightly above MRR
            churn_rate_sim = 0.20 - (self.mrr / 50000 * 0.17) # Decreases with MRR
            cac_sim = 50.0 - (self.mrr / 50000 * 40.0) # Decreases with MRR
            ltv_sim = cac_sim * (1.0 + (self.mrr / 50000 * 3.0)) # Increases with MRR

            data = {
                "mrr": self.mrr, # Use actual MRR
                "revenue": revenue_sim,
                "churn_rate": max(0.01, churn_rate_sim),
                "cac": max(10.0, cac_sim),
                "ltv": max(50.0, ltv_sim),
                "conversion_rate": min(0.05, conversion_rate_sim),
                "visitor_traffic": visitor_traffic
            }
            analysis_result = self.tools["data_analyzer"].analyze(data)
            self.log_action("Analyzed performance data", "data_analyzer", outcome=f"Analysis: {analysis_result['current_phase']} - {analysis_result['recommendations'][0] if analysis_result['recommendations'] else 'No specific recommendation.' }")

            # Update MRR phase of agent based on analysis
            self.phase = analysis_result['current_phase']
            # This is where agent would act on recommendations or phase progression
            if analysis_result['phase_progression'] == 'advance':
                self.log_action(f"Data analysis suggests to advance phase: {analysis_result['recommendations'][0]}")
                return self.make_decision("move to next phase")
            elif "Prioritize A/B testing" in (analysis_result['recommendations'][0] if analysis_result['recommendations'] else '') and self.current_objective_index > 1:
                return self.execute_action("generate_marketing_content") # Simulate A/B test by generating new content
            elif "Review customer acquisition" in (analysis_result['recommendations'][0] if analysis_result['recommendations'] else '') and self.current_objective_index > 1:
                return self.execute_action("launch_marketing_campaign") # Re-launch/adjust campaign


        elif action == "launch_marketing_campaign":
            cost = 50.0
            add_mrr_impact = 100.0 + (self.mrr * 0.1) # Simulate MRR gain from campaign
            # Ensure mrr passed to deduct_funds is current self.mrr
            deduct_response = self.budget_manager.deduct_funds(cost, description="Marketing Campaign", mrr=self.mrr)
            if deduct_response["status"] == "success":
                self.log_action("Launched marketing campaign", cost=cost)
                add_response = self.budget_manager.add_funds(add_mrr_impact * 2, description="Revenue from campaign (simulated)", mrr_impact=add_mrr_impact)
                self.revenue += add_mrr_impact * 2 # Keep for legacy tracking, MRR is primary
                self.mrr += add_mrr_impact
                self.log_action("Generated revenue from marketing", revenue_impact=add_mrr_impact*2, outcome=f"New MRR: ${add_mrr_impact:.2f}")
                return self.make_decision("evaluate current revenue and strategy")
            else:
                self.log_action("Attempted marketing campaign", cost=cost, outcome=f"Failed: {deduct_response['message']}")

        elif action == "optimize_and_scale":
            cost = 20.0 # Simulate re-investment cost
            add_mrr_impact = 200.0 + (self.mrr * 0.15) # Simulate larger MRR gain from optimization
            deduct_response = self.budget_manager.deduct_funds(cost, description="Optimization & Scaling", mrr=self.mrr)
            if deduct_response["status"] == "success":
                self.log_action("Optimizing operations for scaling", cost=cost)
                add_response = self.budget_manager.add_funds(add_mrr_impact * 2, description="Revenue from scaling (simulated)", mrr_impact=add_mrr_impact)
                self.revenue += add_mrr_impact * 2
                self.mrr += add_mrr_impact
                self.log_action("Scaled operations and generated more revenue", revenue_impact=add_mrr_impact*2, outcome=f"MRR increased by ${add_mrr_impact:.2f}")
                if self.mrr >= 50000.0: return self.make_decision("mission_accomplished")
                else: return self.make_decision("evaluate current revenue and strategy")
            else:
                self.log_action("Attempted optimization and scaling", cost=cost, outcome=f"Failed: {deduct_response['message']}")

        elif action == "mission_accomplished":
            self.log_action("AgentWill has achieved its goal: $50,000 MRR!")
            return False # Signal to stop execution

        elif action == "evaluate_current_strategy":
            self.log_action("Evaluating current strategy and progress...")
            # Trigger detailed performance analysis
            return self.execute_action("analyze_performance")

        # If no specific action, still return True to continue loop, or False to stop if stuck
        return True

    def run(self):
        self.log_action("AgentWill starting its autonomous operation.")
        executable = True
        while executable and self.mrr < 50000.0:
            current_objective = self.objectives[self.current_objective_index]
            
            # Fetch latest budget status and update internal MRR if necessary (from budget_manager's loaded state)
            # For now, agent_will's self.mrr is the source of truth, but would ideally be synced.
            budget_status_response = self.budget_manager.check_budget_status(self.mrr)
            self.phase = budget_status_response['current_mrr_phase'] # Keep AgentWill's phase updated
            current_budget = budget_status_response['current_balance']

            context = f"Current objective: {current_objective}. Current MRR: ${self.mrr:.2f}. Budget: ${current_budget:.2f}. Phase: {self.phase}. What action should be taken? " \
                       f"Consider if current phase ({self.phase}) is complete or if more actions are needed to fulfill the objective."
            
            action_to_take = self.make_decision(context)

            if action_to_take == "mission_accomplished":
                executable = False
                continue

            last_mrr = self.mrr
            last_budget = current_budget
            
            executable = self.execute_action(action_to_take)

            if not executable: # If execute_action explicitly returned False (e.g., mission accomplished)
                break

            # Add a break condition if the agent seems to be stuck without making progress
            if self.mrr == last_mrr and self.budget_manager.current_budget == last_budget and action_to_take == "evaluate_current_strategy":
                self.log_action("Agent seems stuck without progress after evaluation and no change in MRR/Budget.", outcome="Halted")
                executable = False

            time.sleep(0.5) # Simulate time passing between actions

        if self.mrr >= 50000.0:
            self.log_action("Target MRR achieved! AgentWill operation concluded.")
        else:
            self.log_action("AgentWill stopped before reaching target, possibly due to budget constraints, logic loop, or early termination.")

if __name__ == "__main__":
    agent = AgentWill()
    agent.run()


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
        self.budget_manager = BudgetManager(INITIAL_BUDGET)
        self.tools = {
            "web_search": WebSearchTool(),
            "content_generator": ContentGeneratorTool(),
            "data_analyzer": DataAnalyzerTool()
        }
        self.revenue = 0.0
        self.phase = "Initialization"
        self.objectives = [
            "Identify a viable market niche",
            "Develop an MVP",
            "Acquire first paying customers",
            "Scale revenue to $50,000/month"
        ]
        self.current_objective_index = 0
        self.log_action(f"Agent {self.name} initialized with budget ${self.budget_manager.get_current_budget():.2f}")

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
            "current_revenue": self.revenue,
            "current_budget": self.budget_manager.get_current_budget()
        }
        with open(LOG_FILE, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
        print(f"[{timestamp}] {self.name} ({self.phase}): {action_description} [Revenue: ${self.revenue:.2f}, Budget: ${self.budget_manager.get_current_budget():.2f}]")

    def make_decision(self, context):
        # A placeholder for advanced LLM-driven decision making
        # In a real OpenClaw agent, this would involve complex reasoning
        # using an LLM to choose the best action based on context, objectives, and tool capabilities.
        self.log_action(f"Analyzing context for decision: {context}")

        if "market research" in context.lower() and self.current_objective_index == 0:
            return "perform_market_research"
        elif "create content" in context.lower():
            return "generate_marketing_content"
        elif "analyze data" in context.lower():
            return "analyze_performance"
        elif self.revenue >= 50000.0 and self.current_objective_index == len(self.objectives) - 1:
            return "mission_accomplished"
        elif "next objective" in context.lower() or "move to next phase" in context.lower():
            if self.current_objective_index < len(self.objectives) - 1:
                self.current_objective_index += 1
                self.phase = f"Phase {self.current_objective_index + 1}"
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
            if self.budget_manager.can_afford(cost):
                self.budget_manager.deduct_funds(cost)
                results = self.tools["web_search"].search("market trends, unmet needs, competitor analysis")
                self.log_action("Performed market research", "web_search", cost=cost, outcome=f"Found {len(results)} search results.")
                # After research, simulate a decision to move to MVP or further analyze
                # For now, let's simulate that research is 'done' and we are ready for next phase
                if self.current_objective_index == 0: # If still in market research phase
                    # This is a good spot for a more complex decision, but for now, just advance
                    self.log_action("Market research completed, ready to define MVP.", outcome="Success")
                    return self.make_decision("move to next phase")
            else:
                self.log_action("Attempted market research", tool_used="web_search", cost=cost, outcome="Failed: Insufficient budget.")

        elif action == "design_and_build_mvp":
            cost = 100.0 # Simulate MVP development cost
            if self.budget_manager.can_afford(cost):
                self.budget_manager.deduct_funds(cost)
                self.log_action("Designed and built MVP", cost=cost, outcome="MVP ready for launch.")
                # After MVP is built, move to customer acquisition
                return self.make_decision("move to next phase")
            else:
                self.log_action("Attempted MVP development", cost=cost, outcome="Failed: Insufficient budget.")

        elif action == "generate_marketing_content":
            cost = 5.0 # Simulate content generation cost
            if self.budget_manager.can_afford(cost):
                self.budget_manager.deduct_funds(cost)
                content = self.tools["content_generator"].generate_text("short marketing slogan for a new SaaS product")
                self.log_action("Generated marketing content", "content_generator", cost=cost, outcome=f"Content: {content[:50]}...")
            else:
                self.log_action("Attempted content generation", tool_used="content_generator", cost=cost, outcome="Failed: Insufficient budget.")

        elif action == "analyze_performance":
            # Simulate getting data from a 'live' MVP or marketing campaign
            # This example generates dummy data for simplicity
            data = {"visitors": 100 + int(self.revenue/10), "conversions": 5 + int(self.revenue/50), "revenue": self.revenue}
            analysis = self.tools["data_analyzer"].analyze(data)
            self.log_action("Analyzed performance data", "data_analyzer", outcome=f"Analysis: {analysis['summary']} Recommendation: {analysis['recommendation']}")
            if analysis.get('recommendation') == 'increase marketing' and self.current_objective_index > 1:
                # If we're past MVP and need more revenue, launch campaign
                return self.execute_action("launch_marketing_campaign")

        elif action == "launch_marketing_campaign":
            cost = 50.0
            if self.budget_manager.can_afford(cost):
                self.budget_manager.deduct_funds(cost)
                self.log_action("Launched marketing campaign", cost=cost)
                # Simulate revenue generation based on campaign
                revenue_gain = 150.0 + (self.current_objective_index * 50) # Simulate increasing returns in later phases
                self.revenue += revenue_gain
                self.budget_manager.add_funds(revenue_gain, description="Revenue from campaign")
                self.log_action("Generated revenue from marketing", revenue_impact=revenue_gain, outcome=f"New revenue: ${revenue_gain:.2f}")
                # After generating revenue, re-evaluate or push towards next phase
                return self.make_decision("evaluate current revenue and strategy")
            else:
                self.log_action("Attempted marketing campaign", cost=cost, outcome="Failed: Insufficient budget.")

        elif action == "optimize_and_scale":
            cost = 20.0 # Simulate re-investment cost
            if self.budget_manager.can_afford(cost):
                self.budget_manager.deduct_funds(cost)
                self.log_action("Optimizing operations for scaling", cost=cost)
                # Simulate a larger revenue jump due to optimization
                revenue_gain = 500.0 + (self.revenue * 0.1)
                self.revenue += revenue_gain
                self.budget_manager.add_funds(revenue_gain, description="Revenue from scaling")
                self.log_action("Scaled operations and generated more revenue", revenue_impact=revenue_gain, outcome=f"Revenue increased by ${revenue_gain:.2f}")
                # After scaling, check if target is met or continue scaling
                if self.revenue >= 50000.0: return self.make_decision("mission accomplished")
                else: return self.make_decision("evaluate current revenue and strategy")
            else:
                self.log_action("Attempted optimization and scaling", cost=cost, outcome="Failed: Insufficient budget.")

        elif action == "mission_accomplished":
            self.log_action("AgentWill has achieved its goal: $50,000 MRR!")
            return False # Signal to stop execution

        elif action == "evaluate_current_strategy":
            self.log_action("Evaluating current strategy and progress...")
            if self.revenue < 50000.0 and self.current_objective_index < len(self.objectives) - 1:
                # If not at target and not at final objective, try to progress to next or repeat current
                if self.current_objective_index == 0: # Still in market research, assume it needs to complete
                    return self.execute_action("perform_market_research")
                elif self.current_objective_index == 1: # Still in MVP phase
                    return self.execute_action("design_and_build_mvp")
                elif self.current_objective_index == 2: # In customer acquisition phase, needs more campaigns
                    return self.execute_action("launch_marketing_campaign")
                elif self.current_objective_index == 3: # In scaling phase, needs more optimization
                    return self.execute_action("optimize_and_scale")
            elif self.revenue < 50000.0 and self.current_objective_index == len(self.objectives) - 1:
                # If in final phase but not at target, keep optimizing and scaling
                self.log_action("Still below target revenue in final phase, continuing optimization.")
                return self.execute_action("optimize_and_scale")

        # If no specific action, still return True to continue loop, or False to stop if stuck
        return True

    def run(self):
        self.log_action("AgentWill starting its autonomous operation.")
        executable = True
        while executable and self.revenue < 50000.0:
            current_objective = self.objectives[self.current_objective_index]
            self.phase = f"Phase {self.current_objective_index + 1}: {current_objective}"
            context = f"Current objective: {current_objective}. Current revenue: ${self.revenue:.2f}. Budget: ${self.budget_manager.get_current_budget():.2f}. What action should be taken? " \
                       f"Consider if current phase is complete or if more actions are needed to fulfill the objective."
            
            action_to_take = self.make_decision(context)

            if action_to_take == "mission_accomplished":
                executable = False
                continue

            # Ensure the agent doesn't get stuck in an endless loop of 'evaluate_current_strategy'
            last_revenue = self.revenue
            last_budget = self.budget_manager.get_current_budget()
            
            executable = self.execute_action(action_to_take)

            if not executable: # If execute_action explicitly returned False (e.g., mission accomplished)
                break

            # Add a break condition if the agent seems to be stuck without making progress (e.g., budget, or action loop)
            # This is a simplistic check; a real agent would have more sophisticated halting mechanisms.
            if self.revenue == last_revenue and self.budget_manager.get_current_budget() == last_budget and action_to_take == "evaluate_current_strategy":
                self.log_action("Agent seems stuck without progress after evaluation.", outcome="Halted")
                executable = False

            time.sleep(0.5) # Simulate time passing between actions

        if self.revenue >= 50000.0:
            self.log_action("Target revenue achieved! AgentWill operation concluded.")
        else:
            self.log_action("AgentWill stopped before reaching target, possibly due to budget constraints or logic loop.")

if __name__ == "__main__":
    agent = AgentWill()
    agent.run()

import json
import time
import os
import random # Moved to top
from datetime import datetime
from collections import deque # Import deque for action queue
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
        self.phase = "Initialization"
        self.objectives = [
            "Identify a viable market niche",
            "Develop an MVP",
            "Acquire first paying customers",
            "Scale revenue to $50,000/month"
        ]
        self.current_objective_index = 0
        self.action_queue = deque() # Initialize action queue
        self.mrr_history = deque(maxlen=5) # For stuck detection
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
            "current_mrr": self.budget_manager.mrr,
            "current_budget": self.budget_manager.current_budget
        }
        with open(LOG_FILE, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
        print(f"[{timestamp}] {self.name} ({self.phase}): {action_description} [MRR: ${self.budget_manager.mrr:.2f}, Budget: ${self.budget_manager.current_budget:.2f}]")

    def make_decision(self, context):
        # In a real OpenClaw agent, this would involve complex reasoning
        # using an LLM to choose the best action based on context, objectives, and tool capabilities.
        self.log_action(f"Analyzing context for decision: {context}")

        # Update phase based on MRR before making decisions
        budget_status = self.budget_manager.check_budget_status(self.budget_manager.mrr)
        self.phase = budget_status['current_mrr_phase']

        # Simulate LLM-driven ReAct reasoning
        # This is a placeholder for an actual LLM call that would return a structured action.
        # For demonstration, we'll still use some keyword matching but frame it as an LLM output.

        # Example of how an LLM might output a structured action:
        # {"tool": "web_search", "tool_input": {"query": "market trends, unmet needs, competitor analysis"}}
        # {"tool": "content_generator", "tool_input": {"content_type": "marketing_slogan", "prompt": "short marketing slogan for a new SaaS product", "mrr_phase": self.phase}}
        # {"tool": "agent_action", "tool_input": {"action_name": "move_to_next_objective"}}

        if self.budget_manager.mrr >= 50000.0:
            return {"tool": "agent_action", "tool_input": {"action_name": "mission_accomplished"}}

        current_objective_text = self.objectives[self.current_objective_index]

        if "market niche" in current_objective_text and self.current_objective_index == 0:
            return {"tool": "agent_action", "tool_input": {"action_name": "perform_market_research"}}
        elif "MVP" in current_objective_text and self.current_objective_index == 1:
            return {"tool": "agent_action", "tool_input": {"action_name": "design_and_build_mvp"}}
        elif "paying customers" in current_objective_text and self.current_objective_index == 2:
            return {"tool": "agent_action", "tool_input": {"action_name": "launch_marketing_campaign"}}
        elif "$50,000" in current_objective_text and self.current_objective_index == 3:
            return {"tool": "agent_action", "tool_input": {"action_name": "optimize_and_scale"}}
        
        # Default actions if specific objective not met or needs evaluation
        if "evaluate current revenue and strategy" in context.lower() or "analyze performance" in context.lower():
            return {"tool": "agent_action", "tool_input": {"action_name": "analyze_performance"}}
        
        # If current objective is not yet met, try to progress it
        if self.current_objective_index == 0: # Market niche
            return {"tool": "agent_action", "tool_input": {"action_name": "perform_market_research"}}
        elif self.current_objective_index == 1: # MVP
            return {"tool": "agent_action", "tool_input": {"action_name": "design_and_build_mvp"}}
        elif self.current_objective_index == 2: # First paying customers
            return {"tool": "agent_action", "tool_input": {"action_name": "launch_marketing_campaign"}}
        elif self.current_objective_index == 3: # Scale to $50k
            return {"tool": "agent_action", "tool_input": {"action_name": "optimize_and_scale"}}

        context += f' Ethical constraints: {chr(59).join(ETHICAL_GUIDELINES)}'
        return {"tool": "agent_action", "tool_input": {"action_name": "evaluate_current_strategy"}}

    def execute_action(self, action_dict):
        action_type = action_dict.get("tool")
        action_input = action_dict.get("tool_input", {})

        if action_type == "agent_action":
            action = action_input.get("action_name")

            # Get current phase configuration
            budget_status = self.budget_manager.check_budget_status(self.budget_manager.mrr)
            phase_config = budget_status['phase_config']

            if action == "perform_market_research":
                cost = phase_config['market_research_cost'] # Use phase-specific cost
                deduct_response = self.budget_manager.deduct_funds(cost, description="Market Research", mrr=self.budget_manager.mrr)
                if deduct_response["status"] == "success":
                    results = self.tools["web_search"].search("market trends, unmet needs, competitor analysis")
                    self.log_action("Performed market research", "web_search", cost=cost, outcome=f"Found {len(results)} search results.")
                    if self.current_objective_index == 0:
                        self.log_action("Market research completed, ready to define MVP.", outcome="Success")
                        self.action_queue.appendleft({"tool": "agent_action", "tool_input": {"action_name": "move_to_next_objective"}})
                    return True
                else:
                    self.log_action("Attempted market research", tool_used="web_search", cost=cost, outcome=f"Failed: {deduct_response['message']}")
                    self.action_queue.appendleft({"tool": "agent_action", "tool_input": {"action_name": "evaluate_current_strategy"}})
                    return True

            elif action == "design_and_build_mvp":
                cost = phase_config['mvp_development_cost'] # Use phase-specific cost
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
                cost = phase_config['content_generation_cost'] # Use phase-specific cost
                deduct_response = self.budget_manager.deduct_funds(cost, description="Content Generation", mrr=self.budget_manager.mrr)
                if deduct_response["status"] == "success":
                    content_gen_output = self.tools["content_generator"].execute(
                        content_type="marketing_slogan", 
                        prompt="short marketing slogan for a new SaaS product", 
                        mrr_phase=self.phase # Pass self.phase directly
                    )
                    generated_content = f"Slogan: {content_gen_output['generation_prompt'][:50]}..."
                    self.log_action("Generated marketing content", "content_generator", cost=cost, outcome=f"Content: {generated_content}")
                    return True
                else:
                    self.log_action("Attempted content generation", tool_used="content_generator", cost=cost, outcome=f"Failed: {deduct_response['message']}")
                    self.action_queue.appendleft({"tool": "agent_action", "tool_input": {"action_name": "evaluate_current_strategy"}})
                    return True

            elif action == "analyze_performance":
                # Simulate getting data from a 'live' MVP or marketing campaign
                current_mrr = self.budget_manager.mrr
                
                visitor_traffic = phase_config['visitor_traffic_base'] + int(current_mrr * phase_config['visitor_traffic_mrr_factor'])
                conversion_rate_sim = phase_config['conversion_rate_base'] + (current_mrr / 50000 * phase_config['conversion_rate_growth'])
                churn_rate_sim = phase_config['churn_rate_base'] - (current_mrr / 50000 * phase_config['churn_rate_reduction'])
                cac_sim = phase_config['cac_base'] - (current_mrr / 50000 * phase_config['cac_reduction'])
                ltv_sim = cac_sim * (1.0 + (current_mrr / 50000 * phase_config['ltv_growth_factor']))

                data = {
                    "mrr": current_mrr,
                    "revenue": current_mrr * 1.1, # Simulate total revenue slightly above MRR
                    "churn_rate": max(0.01, churn_rate_sim),
                    "cac": max(10.0, cac_sim),
                    "ltv": max(50.0, ltv_sim),
                    "conversion_rate": min(0.05, conversion_rate_sim),
                    "visitor_traffic": visitor_traffic
                }
                analysis_result = self.tools["data_analyzer"].analyze(data)
                self.log_action("Analyzed performance data", "data_analyzer", outcome=f"Analysis: {analysis_result['current_phase']} - {analysis_result['recommendations'][0] if analysis_result['recommendations'] else 'No specific recommendation.' }")

                self.phase = analysis_result['current_phase']
                if analysis_result['phase_progression'] == 'advance':
                    self.log_action(f"Data analysis suggests to advance phase: {analysis_result['recommendations'][0]}")
                    self.action_queue.appendleft({"tool": "agent_action", "tool_input": {"action_name": "move_to_next_objective"}})
                elif "Prioritize A/B testing" in (analysis_result['recommendations'][0] if analysis_result['recommendations'] else '') and self.current_objective_index > 1:
                    self.action_queue.appendleft({"tool": "agent_action", "tool_input": {"action_name": "generate_marketing_content"}}) # Simulate A/B test by generating new content
                elif "Review customer acquisition" in (analysis_result['recommendations'][0] if analysis_result['recommendations'] else '') and self.current_objective_index > 1:
                    self.action_queue.appendleft({"tool": "agent_action", "tool_input": {"action_name": "launch_marketing_campaign"}}) # Re-launch/adjust campaign
                return True

            elif action == "launch_marketing_campaign":
                current_mrr = self.budget_manager.mrr
                
                cost = phase_config['campaign_cost']
                
                deduct_response = self.budget_manager.deduct_funds(cost, description="Marketing Campaign", mrr=current_mrr)
                if deduct_response["status"] == "success":
                    self.log_action("Launched marketing campaign", cost=cost)
                    
                    # Simulate MRR gain based on phase configuration
                    mrr_gain_factor = phase_config['mrr_growth_factor']
                    campaign_success_prob = phase_config['campaign_success_probability']

                    if random.random() < campaign_success_prob: # Simulate campaign success
                        add_mrr_impact = current_mrr * mrr_gain_factor + phase_config['base_mrr_gain']
                        add_response = self.budget_manager.add_funds(add_mrr_impact * 2, description="Revenue from campaign (simulated)", mrr_impact=add_mrr_impact)
                        self.log_action("Generated revenue from marketing", revenue_impact=add_mrr_impact*2, outcome=f"New MRR: ${add_mrr_impact:.2f}")
                    else:
                        add_mrr_impact = phase_config['base_mrr_gain'] * 0.1 # Small gain even if not fully successful
                        add_response = self.budget_manager.add_funds(add_mrr_impact * 2, description="Revenue from campaign (simulated - partial success)", mrr_impact=add_mrr_impact)
                        self.log_action("Marketing campaign had limited success", revenue_impact=add_mrr_impact*2, outcome=f"MRR increased by ${add_mrr_impact:.2f}")

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

                    add_response = self.budget_manager.add_funds(add_mrr_impact * 2, description="Revenue from scaling (simulated)", mrr_impact=add_mrr_impact)
                    self.log_action("Scaled operations and generated more revenue", revenue_impact=add_mrr_impact*2, outcome=f"MRR increased by ${add_mrr_impact:.2f}")
                    if self.budget_manager.mrr >= 50000.0: 
                        self.action_queue.appendleft({"tool": "agent_action", "tool_input": {"action_name": "mission_accomplished"}})
                    else: 
                        self.action_queue.appendleft({"tool": "agent_action", "tool_input": {"action_name": "evaluate_current_strategy"}})
                    return True
                else:
                    self.log_action("Attempted optimization and scaling", cost=cost, outcome=f"Failed: {deduct_response['message']}")
                    self.action_queue.appendleft({"tool": "agent_action", "tool_input": {"action_name": "evaluate_current_strategy"}})
                    return True

            elif action == "mission_accomplished":
                self.log_action("AgentWill has achieved its goal: $50,000 MRR!")
                return False # Signal to stop execution

            elif action == "evaluate_current_strategy":
                self.log_action("Evaluating current strategy and progress...")
                self.action_queue.appendleft({"tool": "agent_action", "tool_input": {"action_name": "analyze_performance"}})
                return True
            
            elif action == "move_to_next_objective":
                if self.current_objective_index < len(self.objectives) - 1:
                    self.current_objective_index += 1
                    self.log_action(f"Moving to next objective: {self.objectives[self.current_objective_index]}")
                    return True # Continue with the new objective
                else:
                    self.action_queue.appendleft({"tool": "agent_action", "tool_input": {"action_name": "mission_accomplished"}})
                    return True

        # If no specific action, still return True to continue loop, or False to stop if stuck
        return True

    def run(self):
        self.log_action("AgentWill starting its autonomous operation.")
        executable = True
        while executable and self.budget_manager.mrr < 50000.0:
            if not self.action_queue:
                # If queue is empty, make a new decision
                current_objective = self.objectives[self.current_objective_index]
                
                budget_status_response = self.budget_manager.check_budget_status(self.budget_manager.mrr)
                self.phase = budget_status_response['current_mrr_phase'] # Keep AgentWill's phase updated
                current_budget = budget_status_response['current_balance']

                context = f"Current objective: {current_objective}. Current MRR: ${self.budget_manager.mrr:.2f}. Budget: ${current_budget:.2f}. Phase: {self.phase}. What action should be taken? " \
                           f"Consider if current phase ({self.phase}) is complete or if more actions are needed to fulfill the objective."
                
                action_to_take = self.make_decision(context)
                self.action_queue.append(action_to_take)
            
            action_to_execute = self.action_queue.popleft()

            if action_to_execute.get("tool_input", {}).get("action_name") == "mission_accomplished":
                executable = False
                continue

            # Record MRR before executing action for stuck detection
            self.mrr_history.append(self.budget_manager.mrr)
            
            executable = self.execute_action(action_to_execute)

            if not executable: # If execute_action explicitly returned False (e.g., mission accomplished)
                break

            # Stuck detection: if MRR hasn't changed for the last 5 iterations
            # Only activate stuck detection once the agent is past the initial pre-revenue objectives
            if self.current_objective_index >= 2 and \
               len(self.mrr_history) == self.mrr_history.maxlen and \
               all(mrr == self.mrr_history[0] for mrr in self.mrr_history):
                self.log_action("Agent seems stuck: MRR has not changed for 5 consecutive actions.", outcome="Halted")
                executable = False

            time.sleep(0.5) # Simulate time passing between actions

        if self.budget_manager.mrr >= 50000.0:
            self.log_action("Target MRR achieved! AgentWill operation concluded.")
        else:
            self.log_action("AgentWill stopped before reaching target, possibly due to budget constraints, logic loop, or early termination.")

if __name__ == "__main__":
    agent = AgentWill()
    agent.run()

import json
import os
from datetime import datetime

LOG_FILE = "logs/budget_manager.log"

class BudgetManager:
    def __init__(self):
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        self.current_budget = 0.0
        self.transactions = [] # Not used for persistence, just for immediate session
        self.load_state()

    def _log_transaction(self, transaction_data):
        with open(LOG_FILE, 'a') as f:
            f.write(json.dumps(transaction_data) + '\n')

    def load_state(self):
        last_balance = 0.0
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'r') as f:
                for line in f:
                    try:
                        transaction = json.loads(line)
                        if transaction['type'] == 'restore':
                            last_balance = float(transaction['amount'])
                        elif transaction['type'] == 'expense':
                            last_balance -= float(transaction['amount'])
                        elif transaction['type'] == 'revenue':
                            last_balance += float(transaction['amount'])
                    except json.JSONDecodeError:
                        continue # Skip malformed lines
        self.current_budget = last_balance
        # Log initial restore for traceability
        self._log_transaction({"type": "restore", "amount": self.current_budget, "timestamp": datetime.now().isoformat(), "description": "Budget restored on startup"})

    def _get_current_phase_and_recommendation(self):
        # Placeholder for dynamic phase logic and recommendations
        # In a real scenario, this would involve more sophisticated logic
        # based on MRR, user activity, etc.
        if self.current_budget < 1000:
            current_phase = "Early Seed"
            recommendation = "Focus on essential R&D and customer acquisition. Limit marketing spend."
        elif self.current_budget < 10000:
            current_phase = "Growth Spark"
            recommendation = "Allocate funds towards scalable marketing channels and product enhancements."
        else:
            current_phase = "Expansion Drive"
            recommendation = "Consider reinvesting in team expansion, new market entry, or advanced infrastructure."
        return current_phase, recommendation

    def _get_response_dict(self):
        current_phase, recommendation = self._get_current_phase_and_recommendation()
        return {
            "status": "success",
            "current_balance": round(self.current_budget, 2),
            "current_phase": current_phase,
            "recommendation": recommendation
        }

    def check_budget_status(self):
        """Checks the current budget, MRR phase, and provides reinvestment recommendations."""
        return self._get_response_dict()

    def add_funds(self, amount: float, description: str = "Revenue"):
        """Adds funds to the budget.

        Args:
            amount (float): The amount to add.
            description (str): A description of the revenue.
        """
        if amount <= 0:
            return {"status": "error", "message": "Amount must be positive."}

        self.current_budget += amount
        transaction = {"type": "revenue", "amount": amount, "description": description, "timestamp": datetime.now().isoformat()}
        self._log_transaction(transaction)
        return self._get_response_dict()

    def deduct_funds(self, amount: float, description: str = "Expense"):
        """Deducts funds from the budget if available.

        Args:
            amount (float): The amount to deduct.
            description (str): A description of the expense.
        """
        if amount <= 0:
            return {"status": "error", "message": "Amount must be positive."}

        if self.current_budget < amount:
            return {
                "status": "error",
                "message": f"Insufficient funds. Available: {self.current_budget:.2f}, Needed: {amount:.2f}"
            }

        self.current_budget -= amount
        transaction = {"type": "expense", "amount": amount, "description": description, "timestamp": datetime.now().isoformat()}
        self._log_transaction(transaction)
        return self._get_response_dict()


# OpenClaw Tool Schema
def get_tool_schema():
    return {
        "budget_manager": {
            "name": "budget_manager",
            "description": "Manages the operational budget, tracks funds, and provides financial insights based on the current MRR phase.",
            "actions": {
                "check_budget_status": {
                    "description": "Checks the current budget, operational phase, and provides reinvestment recommendations.",
                    "parameters": {}
                },
                "add_funds": {
                    "description": "Adds funds to the current budget.",
                    "parameters": {
                        "amount": {
                            "type": "number",
                            "description": "The amount of funds to add."
                        },
                        "description": {
                            "type": "string",
                            "description": "A brief description of the revenue source.",
                            "default": "Revenue"
                        }
                    },
                    "required": ["amount"]
                },
                "deduct_funds": {
                    "description": "Deducts funds from the current budget.",
                    "parameters": {
                        "amount": {
                            "type": "number",
                            "description": "The amount of funds to deduct."
                        },
                        "description": {
                            "type": "string",
                            "description": "A brief description of the expense.",
                            "default": "Expense"
                        }
                    },
                    "required": ["amount"]
                }
            }
        }
    }

if __name__ == '__main__':
    # Example usage for testing
    bm = BudgetManager()
    print(f"Initial status: {bm.check_budget_status()}")

    print(f"Adding $5000: {bm.add_funds(5000, 'Initial Capital')}")
    print(f"Adding $250.75: {bm.add_funds(250.75, 'Monthly Subscription MRR')}")
    print(f"Deducting $120.50: {bm.deduct_funds(120.50, 'Cloud Hosting')}")
    print(f"Deducting $3000: {bm.deduct_funds(3000, 'Marketing Campaign')}")
    print(f"Attempting to deduct too much: {bm.deduct_funds(10000, 'Big Purchase')}")
    print(f"Final status: {bm.check_budget_status()}")

    # Simulate restart
    print("\nSimulating restart...")
    del bm
    bm2 = BudgetManager()
    print(f"Status after restart: {bm2.check_budget_status()}")


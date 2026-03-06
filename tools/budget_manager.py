import json
import os
from datetime import datetime

LOG_FILE = "logs/budget_manager.log"

class BudgetManager:
    PHASE_SPEND_CEILINGS = {
        "discovery_0_100": 500.0,      # Max spend in initial discovery phase
        "validation_100_1k": 2500.0,   # Max spend in validation phase
        "growth_1k_5k": 10000.0,     # Max spend in early growth
        "scaling_5k_20k": 30000.0,   # Max spend in scaling phase
        "expansion_20k_50k": 100000.0, # Max spend in expansion phase
        "mature_50k_plus": float('inf') # No spend limit in mature phase
    }

    BUSINESS_PHASES = {
        "discovery_0_100": {"min_mrr": 0, "max_mrr": 100},
        "validation_100_1k": {"min_mrr": 100, "max_mrr": 1000},
        "growth_1k_5k": {"min_mrr": 1000, "max_mrr": 5000},
        "scaling_5k_20k": {"min_mrr": 5000, "max_mrr": 20000},
        "expansion_20k_50k": {"min_mrr": 20000, "max_mrr": 50000},
        "mature_50k_plus": {"min_mrr": 50000, "max_mrr": float('inf')},
    }

    def __init__(self, initial_budget=0.0):
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        self.current_budget = 0.0
        self.mrr = 0.0 # Initialize MRR
        self.transactions = [] # Not used for persistence, just for immediate session
        self.load_state(initial_budget)

    def _log_transaction(self, transaction_data):
        with open(LOG_FILE, 'a') as f:
            f.write(json.dumps(transaction_data) + '\n')

    def load_state(self, initial_budget):
        last_balance = initial_budget  # Start with the initial budget passed in
        self.mrr = 0.0 # Reset MRR for re-calculation during state load
        restore_logged = False

        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'r') as f:
                for line in f:
                    try:
                        transaction = json.loads(line)
                        if transaction['type'] == 'restore':
                            # 'Restore' entries are for traceability only. No financial impact during replay
                            restore_logged = True
                            continue 
                        elif transaction['type'] == 'expense':
                            last_balance -= float(transaction['amount'])
                        elif transaction['type'] == 'revenue':
                            last_balance += float(transaction['amount'])
                            # Reconstruct MRR by summing all mrr_impact from revenue transactions
                            if 'mrr_impact' in transaction:
                                self.mrr += float(transaction['mrr_impact'])

                        self.transactions.append(transaction) # Keep transactions for session, if needed
                    except json.JSONDecodeError:
                        continue # Skip malformed lines
        self.current_budget = last_balance
        # Log initial restore for traceability if it hasn't been logged yet
        if not restore_logged:
            self._log_transaction({"type": "restore", "amount": initial_budget, "timestamp": datetime.now().isoformat(), "description": "Budget restored/initialized on startup"})


    def _get_current_phase(self, mrr):
        for phase_name, thresholds in self.BUSINESS_PHASES.items():
            if thresholds["min_mrr"] <= mrr < thresholds["max_mrr"]:
                return phase_name
        return "mature_50k_plus" # Fallback for MRR greater than 50k

    def _get_current_phase_and_recommendation(self, mrr: float):
        current_phase = self._get_current_phase(mrr)
        
        recommendation = "Monitor performance and manage budget diligently."
        if current_phase == "discovery_0_100":
            recommendation = "Focus on essential R&D and customer acquisition. Limit marketing spend to validate product-market fit."
        elif current_phase == "validation_100_1k":
            recommendation = "Allocate funds towards scalable marketing channels and product enhancements. Prioritize retention."
        elif current_phase == "growth_1k_5k":
            recommendation = "Increase investment in proven acquisition channels and explore new markets. Consider team expansion."
        elif current_phase == "scaling_5k_20k":
            recommendation = "Optimize operations for efficiency and invest in advanced infrastructure. Expand customer support."
        elif current_phase == "expansion_20k_50k":
            recommendation = "Consider strategic acquisitions, significant market entry, or new product lines. Focus on long-term value."
        elif current_phase == "mature_50k_plus":
            recommendation = "Innovate and diversify your offerings. Explore new ventures or solidify market leadership."
            
        return current_phase, recommendation

    def _get_response_dict(self, mrr: float):
        current_phase, recommendation = self._get_current_phase_and_recommendation(mrr)
        return {
            "status": "success",
            "current_balance": round(self.current_budget, 2),
            "current_mrr_phase": current_phase,
            "recommendation": recommendation
        }

    def check_budget_status(self, mrr: float = 0.0):
        """Checks the current budget, MRR phase, and provides reinvestment recommendations."""
        self.mrr = mrr
        return self._get_response_dict(self.mrr)

    def add_funds(self, amount: float, description: str = "Revenue", mrr_impact: float = 0.0):
        """Adds funds to the budget.

        Args:
            amount (float): The amount to add.
            description (str): A description of the revenue.
            mrr_impact (float): The amount of this revenue that contributes to Monthly Recurring Revenue.
        """
        if amount <= 0:
            return {"status": "error", "message": "Amount must be positive."}

        self.current_budget += amount
        self.mrr += mrr_impact
        transaction = {"type": "revenue", "amount": amount, "description": description, "timestamp": datetime.now().isoformat(), "mrr_impact": mrr_impact}
        self._log_transaction(transaction)
        return self._get_response_dict(self.mrr)

    def deduct_funds(self, amount: float, description: str = "Expense", mrr: float = 0.0):
        """Deducts funds from the budget if available, respecting phase-specific spend ceilings.

        Args:
            amount (float): The amount to deduct.
            description (str): A description of the expense.
            mrr (float): The current monthly recurring revenue, used to determine the operational phase.
        """
        if amount <= 0:
            return {"status": "error", "message": "Amount must be positive."}

        if self.current_budget < amount:
            return {
                "status": "error",
                "message": f"Insufficient funds. Available: {self.current_budget:.2f}, Needed: {amount:.2f}"
            }
        
        current_phase = self._get_current_phase(mrr)
        spend_ceiling = self.PHASE_SPEND_CEILINGS.get(current_phase, float('inf'))

        if amount > spend_ceiling and current_phase != "mature_50k_plus":
            return {
                "status": "error",
                "message": f"Spending ${amount:.2f} exceeds the allowed spend ceiling of ${spend_ceiling:.2f} for the {current_phase} phase. Consider reducing the expense or gaining more MRR to advance to a higher spending phase.",
                "current_balance": round(self.current_budget, 2),
                "current_mrr_phase": current_phase,
                "spend_ceiling_for_phase": spend_ceiling
            }

        self.current_budget -= amount
        transaction = {"type": "expense", "amount": amount, "description": description, "timestamp": datetime.now().isoformat()}
        self._log_transaction(transaction)
        return self._get_response_dict(self.mrr)

    def get_tool_schema(self):
        return {
            "budget_manager": {
                "name": "budget_manager",
                "description": "Manages the operational budget, tracks funds, and provides financial insights based on the current MRR phase.",
                "actions": {
                    "check_budget_status": {
                        "description": "Checks the current budget, operational phase, and provides reinvestment recommendations.",
                        "parameters": {
                            "mrr": {
                                "type": "number",
                                "description": "The current Monthly Recurring Revenue (MRR) of the business. Defaults to 0 if not provided.",
                                "default": 0.0
                            }
                        }
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
                            },
                            "mrr_impact": {
                                "type": "number",
                                "description": "The portion of the added funds that contributes to Monthly Recurring Revenue (MRR). Defaults to 0 if not provided.",
                                "default": 0.0
                            }
                        },
                        "required": ["amount"]
                    },
                    "deduct_funds": {
                        "description": "Deducts funds from the current budget, respecting phase-specific spend ceilings.",
                        "parameters": {
                            "amount": {
                                "type": "number",
                                "description": "The amount of funds to deduct."
                            },
                            "description": {
                                "type": "string",
                                "description": "A brief description of the expense.",
                                "default": "Expense"
                            },
                            "mrr": {
                                "type": "number",
                                "description": "The current Monthly Recurring Revenue (MRR) of the business, used to determine the operational phase for spend ceiling checks. Defaults to 0 if not provided.",
                                "default": 0.0
                            }
                        },
                        "required": ["amount"]
                    }
                }
            }
        }

if __name__ == '__main__':
    # Example usage for testing
    
    # Clean up log file for a fresh start during testing
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)
    
    print("--- Test 1: Initial budget and basic operations ---")
    bm = BudgetManager(initial_budget=100.0)
    print(f"Initial status: {bm.check_budget_status(mrr=0.0)}")

    print(f"Adding $50.00 (MRR impact $50): {bm.add_funds(50.00, 'Seed Investment', mrr_impact=50.0)}") # MRR now 50
    print(f"Deducting $20.00 (discovery phase): {bm.deduct_funds(20.00, 'Market Tool', mrr=50.0)}")
    print(f"Current status: {bm.check_budget_status(mrr=50.0)}")

    print("\n--- Test 2: Exceeding spend ceiling in Discovery Phase ---")
    # Discovery phase ceiling is $500.0
    print(f"Attempting to deduct $500.01 (mrr=50): {bm.deduct_funds(500.01, 'Huge Marketing Campaign', mrr=50.0)}")
    print(f"Current status (after failed deduction): {bm.check_budget_status(mrr=50.0)}")

    print("\n--- Test 3: Advancing MRR and higher spend ---")
    print(f"Adding $1000.00 (MRR impact $1000): {bm.add_funds(1000.00, 'New Client Contracts', mrr_impact=1000.0)}") # MRR now 1050 (Validation phase)
    print(f"Current status (MRR 1050): {bm.check_budget_status(mrr=1050.0)}")
    # Validation phase ceiling is $2500.0
    print(f"Deducting $1200.00 (validation phase): {bm.deduct_funds(1200.00, 'Product Dev', mrr=1050.0)}")
    print(f"Current status: {bm.check_budget_status(mrr=1050.0)}")

    print("\n--- Test 4: Simulating restart and state load ---")
    print("Simulating restart...")
    del bm
    bm2 = BudgetManager(initial_budget=100.0) # Initial budget passed again on restart
    print(f"Status after restart (MRR should reload from logs): {bm2.check_budget_status(mrr=bm2.mrr)}") # Pass mrr from reloaded state
    # Verify current budget is correctly restored from logs
    exp_budget_after_restart = (100.0 + 50.0 + 1000.0) - (20.0 + 1200.0) # initial + revenue - expenses
    print(f"Expected budget after restart: {exp_budget_after_restart:.2f}")
    assert abs(bm2.check_budget_status(mrr=bm2.mrr)['current_balance'] - exp_budget_after_restart) < 0.01

    print("\n--- Test 5: Reaching Expansion Phase and large spend ---")
    print(f"Adding funds to reach expansion phase MRR: {bm2.add_funds(30000.0, 'Major Funding Round', mrr_impact=20000.0)}") # MRR now 21050
    print(f"Current status (MRR 21050): {bm2.check_budget_status(mrr=bm2.mrr)}")
    # Expansion phase ceiling is $100000.0
    print(f"Deducting $15000.00 (expansion phase): {bm2.deduct_funds(15000.00, 'New Market Entry', mrr=bm2.mrr)}")
    print(f"Current status: {bm2.check_budget_status(mrr=bm2.mrr)}")

    print("\n--- Test 6: MRR Impact on restore ---")
    # Ensuring MRR is consistent across restarts
    del bm2
    bm3 = BudgetManager(initial_budget=100.0) # Initial budget passed again on restart
    # MRR should now be correctly loaded internally by BudgetManager
    print(f"Status after restart (MRR should be {bm3.mrr}): {bm3.check_budget_status(mrr=bm3.mrr)}")
    expected_mrr_after_all_adds = 50.0 + 1000.0 + 20000.0
    assert abs(bm3.mrr - expected_mrr_after_all_adds) < 0.01

    print("All budget manager tests passed!")


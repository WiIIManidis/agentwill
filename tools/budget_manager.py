from datetime import datetime

class BudgetManager:
    def __init__(self, initial_budget):
        self.current_budget = initial_budget
        self.transactions = []

    def get_current_budget(self):
        return self.current_budget

    def can_afford(self, amount):
        return self.current_budget >= amount

    def deduct_funds(self, amount, description="Expense"):
        if not self.can_afford(amount):
            raise ValueError(f"Insufficient funds for: {description}. Needed: {amount:.2f}, Available: {self.current_budget:.2f}")
        self.current_budget -= amount
        self.transactions.append({"type": "expense", "amount": amount, "description": description, "timestamp": datetime.now().isoformat()})
        return True

    def add_funds(self, amount, description="Revenue"):
        self.current_budget += amount
        self.transactions.append({"type": "revenue", "amount": amount, "description": description, "timestamp": datetime.now().isoformat()})
        return True

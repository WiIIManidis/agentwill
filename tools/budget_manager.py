import json
from datetime import datetime

class BudgetManager:
    # Define phases and their MRR thresholds
    PHASE_THRESHOLDS = {
        "Seed": 0,
        "Pre-Seed": 100,
        "Series A": 1000,
        "Series B": 10000,
        "Series C": 25000,
        "IPO": 50000 # Target MRR for IPO phase
    }

    # Configuration for each phase, including costs and simulation parameters
    PHASE_CONFIG = {
        "Seed": {
            "market_research_cost": 50.0,
            "mvp_development_cost": 200.0,
            "content_generation_cost": 20.0,
            "campaign_cost": 100.0,
            "optimization_cost": 50.0,
            "base_mrr_gain": 10.0,
            "base_mrr_gain_scale": 0.0,
            "mrr_growth_factor": 0.05,
            "mrr_growth_factor_scale": 0.0,
            "campaign_success_probability": 0.6,
            "visitor_traffic_base": 100,
            "visitor_traffic_mrr_factor": 0.1,
            "conversion_rate_base": 0.005,
            "conversion_rate_growth": 0.001,
            "churn_rate_base": 0.1,
            "churn_rate_reduction": 0.01,
            "cac_base": 50.0,
            "cac_reduction": 5.0,
            "ltv_growth_factor": 0.5
        },
        "Pre-Seed": {
            "market_research_cost": 75.0,
            "mvp_development_cost": 300.0,
            "content_generation_cost": 30.0,
            "campaign_cost": 150.0,
            "optimization_cost": 75.0,
            "base_mrr_gain": 25.0,
            "base_mrr_gain_scale": 0.0,
            "mrr_growth_factor": 0.07,
            "mrr_growth_factor_scale": 0.0,
            "campaign_success_probability": 0.65,
            "visitor_traffic_base": 200,
            "visitor_traffic_mrr_factor": 0.15,
            "conversion_rate_base": 0.007,
            "conversion_rate_growth": 0.0015,
            "churn_rate_base": 0.09,
            "churn_rate_reduction": 0.015,
            "cac_base": 45.0,
            "cac_reduction": 6.0,
            "ltv_growth_factor": 0.6
        },
        "Series A": {
            "market_research_cost": 100.0,
            "mvp_development_cost": 400.0,
            "content_generation_cost": 40.0,
            "campaign_cost": 200.0,
            "optimization_cost": 100.0,
            "base_mrr_gain": 50.0,
            "base_mrr_gain_scale": 0.0,
            "mrr_growth_factor": 0.1,
            "mrr_growth_factor_scale": 0.0,
            "campaign_success_probability": 0.7,
            "visitor_traffic_base": 500,
            "visitor_traffic_mrr_factor": 0.2,
            "conversion_rate_base": 0.01,
            "conversion_rate_growth": 0.002,
            "churn_rate_base": 0.08,
            "churn_rate_reduction": 0.02,
            "cac_base": 40.0,
            "cac_reduction": 7.0,
            "ltv_growth_factor": 0.7
        },
        "Series B": {
            "market_research_cost": 150.0,
            "mvp_development_cost": 600.0,
            "content_generation_cost": 60.0,
            "campaign_cost": 300.0,
            "optimization_cost": 150.0,
            "base_mrr_gain": 100.0,
            "base_mrr_gain_scale": 0.0,
            "mrr_growth_factor": 0.12,
            "mrr_growth_factor_scale": 0.0,
            "campaign_success_probability": 0.75,
            "visitor_traffic_base": 1000,
            "visitor_traffic_mrr_factor": 0.25,
            "conversion_rate_base": 0.015,
            "conversion_rate_growth": 0.0025,
            "churn_rate_base": 0.07,
            "churn_rate_reduction": 0.025,
            "cac_base": 35.0,
            "cac_reduction": 8.0,
            "ltv_growth_factor": 0.8
        },
        "Series C": {
            "market_research_cost": 200.0,
            "mvp_development_cost": 800.0,
            "content_generation_cost": 80.0,
            "campaign_cost": 400.0,
            "optimization_cost": 200.0,
            "base_mrr_gain": 200.0,
            "base_mrr_gain_scale": 0.0,
            "mrr_growth_factor": 0.15,
            "mrr_growth_factor_scale": 0.0,
            "campaign_success_probability": 0.8,
            "visitor_traffic_base": 2000,
            "visitor_traffic_mrr_factor": 0.3,
            "conversion_rate_base": 0.02,
            "conversion_rate_growth": 0.003,
            "churn_rate_base": 0.06,
            "churn_rate_reduction": 0.03,
            "cac_base": 30.0,
            "cac_reduction": 9.0,
            "ltv_growth_factor": 0.9
        },
        "IPO": {
            "market_research_cost": 250.0,
            "mvp_development_cost": 1000.0,
            "content_generation_cost": 100.0,
            "campaign_cost": 500.0,
            "optimization_cost": 250.0,
            "base_mrr_gain": 500.0,
            "base_mrr_gain_scale": 1000.0,
            "mrr_growth_factor": 0.2,
            "mrr_growth_factor_scale": 0.05,
            "campaign_success_probability": 0.85,
            "visitor_traffic_base": 5000,
            "visitor_traffic_mrr_factor": 0.4,
            "conversion_rate_base": 0.025,
            "conversion_rate_growth": 0.0035,
            "churn_rate_base": 0.05,
            "churn_rate_reduction": 0.035,
            "cac_base": 25.0,
            "cac_reduction": 10.0,
            "ltv_growth_factor": 1.0
        },
        "Exit Prep": {
            "market_research_cost": 500.0, # Due diligence
            "mvp_development_cost": 0.0, # Focus shifts from development
            "content_generation_cost": 200.0, # Investor documents
            "campaign_cost": 1000.0, # Legal and broker fees
            "optimization_cost": 300.0, # Financial and operational optimization
            "base_mrr_gain": 1000.0, # Continued growth to maximize valuation
            "base_mrr_gain_scale": 2000.0,
            "mrr_growth_factor": 0.25,
            "mrr_growth_factor_scale": 0.1,
            "campaign_success_probability": 0.9, # High confidence in exit strategy
            "visitor_traffic_base": 10000,
            "visitor_traffic_mrr_factor": 0.5,
            "conversion_rate_base": 0.03,
            "conversion_rate_growth": 0.004,
            "churn_rate_base": 0.04,
            "churn_rate_reduction": 0.04,
            "cac_base": 20.0,
            "cac_reduction": 12.0,
            "ltv_growth_factor": 1.2
        }
    }

    def __init__(self, initial_budget: float):
        self.current_budget = initial_budget
        self.mrr = 0.0  # Monthly Recurring Revenue
        self.transactions = []

    def _record_transaction(self, type: str, amount: float, description: str, mrr_impact: float = 0.0):
        self.transactions.append({
            "timestamp": datetime.now().isoformat(),
            "type": type,
            "amount": amount,
            "description": description,
            "mrr_impact": mrr_impact,
            "current_budget": self.current_budget,
            "current_mrr": self.mrr
        })

    def deduct_funds(self, amount: float, description: str, mrr: float = 0.0) -> dict:
        if self.current_budget >= amount:
            self.current_budget -= amount
            self._record_transaction("deduction", amount, description)
            return {"status": "success", "new_budget": self.current_budget}
        else:
            self._record_transaction("deduction_failed", amount, description)
            return {"status": "failed", "message": "Insufficient funds", "current_budget": self.current_budget}

    def add_funds(self, amount: float, description: str, mrr_impact: float = 0.0) -> dict:
        self.current_budget += amount
        self.mrr += mrr_impact
        self._record_transaction("addition", amount, description, mrr_impact)
        return {"status": "success", "new_budget": self.current_budget, "new_mrr": self.mrr}

    def get_current_status(self) -> dict:
        return {"budget": self.current_budget, "mrr": self.mrr}

    def check_budget_status(self, current_mrr: float) -> dict:
        current_mrr_phase = "Seed"
        for phase, threshold in sorted(self.PHASE_THRESHOLDS.items(), key=lambda item: item[1]):
            if current_mrr >= threshold:
                current_mrr_phase = phase
            else:
                break # MRR is below this phase's threshold
        
        # Get the configuration for the determined phase
        phase_config = self.PHASE_CONFIG.get(current_mrr_phase, self.PHASE_CONFIG["Seed"]) # Default to Seed if not found

        return {
            "current_balance": self.current_budget,
            "current_mrr": current_mrr,
            "current_mrr_phase": current_mrr_phase,
            "phase_config": phase_config
        }

    def get_transaction_history(self) -> list:
        return self.transactions

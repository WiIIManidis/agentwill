import os
import logging
import datetime

# Ensure logs directory exists before configuring FileHandler
os.makedirs("logs", exist_ok=True)

# Setup structured logging for the DataAnalyzerTool
logging.basicConfig(
    filename='logs/data_analyzer.log',
    level=logging.INFO,
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": %(message)s}',
    datefmt='%Y-%m-%d %H:%M:%S'
)


class DataAnalyzerTool:
    BUSINESS_PHASES = {
        "discovery_0_100":    {"min_mrr": 0,     "max_mrr": 100,          "display": "Seed"},
        "validation_100_1k":  {"min_mrr": 100,   "max_mrr": 1000,         "display": "Pre-Seed"},
        "growth_1k_5k":       {"min_mrr": 1000,  "max_mrr": 5000,         "display": "Series A"},
        "scaling_5k_20k":     {"min_mrr": 5000,  "max_mrr": 20000,        "display": "Series B"},
        "expansion_20k_50k":  {"min_mrr": 20000, "max_mrr": 50000,        "display": "Series C"},
        "mature_50k_plus":    {"min_mrr": 50000, "max_mrr": float('inf'), "display": "IPO"},
    }

    BENCHMARKS = {
        "conversion_rate": {
            "discovery_0_100":   0.005,  # 0.5%
            "validation_100_1k": 0.01,   # 1%
            "growth_1k_5k":      0.02,   # 2%
            "scaling_5k_20k":    0.03,   # 3%
            "expansion_20k_50k": 0.04,   # 4%
            "mature_50k_plus":   0.05,   # 5%
        },
        "churn_rate": {
            "discovery_0_100":   0.20,   # 20%
            "validation_100_1k": 0.15,   # 15%
            "growth_1k_5k":      0.10,   # 10%
            "scaling_5k_20k":    0.07,   # 7%
            "expansion_20k_50k": 0.05,   # 5%
            "mature_50k_plus":   0.03,   # 3%
        },
        "cac_ltv_ratio": {
            "discovery_0_100":   0.5,    # LTV/CAC > 0.5
            "validation_100_1k": 1.0,    # LTV/CAC > 1.0
            "growth_1k_5k":      2.0,    # LTV/CAC > 2.0
            "scaling_5k_20k":    3.0,    # LTV/CAC > 3.0
            "expansion_20k_50k": 3.5,    # LTV/CAC > 3.5
            "mature_50k_plus":   4.0,    # LTV/CAC > 4.0
        }
    }

    def _get_current_phase(self, mrr: float) -> str:
        for phase_name, thresholds in self.BUSINESS_PHASES.items():
            if thresholds["min_mrr"] <= mrr < thresholds["max_mrr"]:
                return phase_name
        return "mature_50k_plus"

    def _get_display_phase(self, phase_key: str) -> str:
        """Returns the human-readable phase name matching budget_manager.py conventions."""
        return self.BUSINESS_PHASES.get(phase_key, {}).get("display", phase_key)

    def _validate_data(self, data: dict):
        required_metrics = ["mrr", "revenue", "churn_rate", "cac", "ltv", "conversion_rate", "visitor_traffic"]
        for metric in required_metrics:
            if not isinstance(data.get(metric), (int, float)) or data.get(metric) < 0:
                raise ValueError(f"Invalid or missing metric: '{metric}'. Must be a non-negative number.")
        if data["mrr"] > data["revenue"]:
            logging.warning(f"{{\"message\": \"MRR ({data['mrr']}) is greater than total revenue ({data['revenue']}), potential data discrepancy.\"}}")
        logging.info(f"{{\"message\": \"Input data validated successfully.\", \"data\": {data}}}")

    def get_tool_schema(self) -> dict:
        return {
            "name": "data_analyzer",
            "description": "Analyzes business performance metrics against phase benchmarks and returns issues, recommendations, and phase progression signal.",
            "parameters": {
                "type": "object",
                "properties": {
                    "data": {
                        "type": "object",
                        "description": "Dict containing mrr, revenue, churn_rate, cac, ltv, conversion_rate, visitor_traffic."
                    }
                },
                "required": ["data"]
            }
        }

    def analyze(self, data: dict) -> dict:
        try:
            self._validate_data(data)
        except ValueError as e:
            logging.error(f"{{\"message\": \"Data validation failed\", \"error\": \"{str(e)}\", \"input_data\": {data}}}")
            return {
                "timestamp": datetime.datetime.now().isoformat(),
                "current_mrr": data.get("mrr", 0),
                "current_phase": "N/A",
                "issues": [f"Input data error: {str(e)}"],
                "recommendations": ["Ensure all required business metrics are provided and valid."],
                "phase_progression": "stay"
            }

        mrr = data["mrr"]
        phase_key = self._get_current_phase(mrr)
        display_phase = self._get_display_phase(phase_key)
        phase_threshold_next = self.BUSINESS_PHASES[phase_key]["max_mrr"]

        issues = []
        recommendations = []
        phase_progression = "stay"

        logging.info(f"{{\"message\": \"Starting analysis for MRR: {mrr}, Phase: {display_phase}\", \"data\": {data}}}")

        # Conversion Rate
        expected_cr = self.BENCHMARKS["conversion_rate"].get(phase_key, 0.01)
        if data["conversion_rate"] < expected_cr:
            issues.append(f"Conversion rate ({data['conversion_rate']:.2%}) is below benchmark ({expected_cr:.2%}) for {display_phase} phase.")
            recommendations.append("Prioritize A/B testing landing pages and optimizing conversion funnels.")

        # Churn Rate
        expected_churn = self.BENCHMARKS["churn_rate"].get(phase_key, 0.10)
        if data["churn_rate"] > expected_churn:
            issues.append(f"Churn rate ({data['churn_rate']:.2%}) is above benchmark ({expected_churn:.2%}) for {display_phase} phase.")
            recommendations.append("Focus on customer success and retention strategies. Identify reasons for churn.")

        # CAC/LTV Ratio
        expected_cac_ltv_ratio = self.BENCHMARKS["cac_ltv_ratio"].get(phase_key, 1.0)
        if data["cac"] > 0 and (data["ltv"] / data["cac"]) < expected_cac_ltv_ratio:
            issues.append(f"LTV/CAC ratio ({data['ltv'] / data['cac']:.2f}) is below benchmark ({expected_cac_ltv_ratio:.2f}) for {display_phase} phase.")
            recommendations.append("Review customer acquisition channels for cost-efficiency or improve LTV through upselling/cross-selling.")
        elif data["cac"] == 0 and mrr > 0:
            issues.append("CAC is zero while MRR is present. Verify CAC reporting to understand true acquisition costs.")
            recommendations.append("Ensure accurate tracking of Customer Acquisition Costs.")

        # Revenue/Traffic
        if mrr == 0 and data["revenue"] == 0 and data["visitor_traffic"] > 0:
            issues.append("No revenue or MRR despite visitor traffic. Product-market fit or monetization strategy needs review.")
            recommendations.append("Focus on monetization strategies, value proposition, and user feedback to understand conversion blockers.")

        if mrr < self.BUSINESS_PHASES[phase_key]["min_mrr"]:
            recommendations.append("Review strategy to regain traction and move towards the current phase's minimum MRR.")

        # Phase progression check
        if mrr >= phase_threshold_next and phase_key != "mature_50k_plus":
            phase_progression = "advance"
            recommendations.insert(0, f"Congratulations! Business is ready to advance to the next growth phase (MRR > ${phase_threshold_next - 1}). Prepare to scale operations and iterate on strategy.")
        elif mrr < phase_threshold_next * 0.5 and phase_key != "discovery_0_100":
            phase_progression = "re-evaluate"
            recommendations.append(f"Current MRR (${mrr}) is significantly below the target for advancing to the next phase (${phase_threshold_next}). Consider re-evaluating core strategies.")

        if not issues:
            issues.append("All key metrics are currently on track for the current phase.")
            if phase_progression == "stay":
                recommendations.append("Continue to monitor metrics closely. Explore opportunities for incremental improvements to accelerate growth.")
        if not recommendations:
            recommendations.append("Monitor business performance and look for opportunities to optimize.")

        analysis_result = {
            "timestamp": datetime.datetime.now().isoformat(),
            "current_mrr": mrr,
            "current_phase": display_phase,  # human-readable, matches budget_manager.py
            "issues": sorted(list(set(issues))),
            "recommendations": sorted(list(set(recommendations)), reverse=True),
            "phase_progression": phase_progression
        }
        logging.info(f"{{\"message\": \"Analysis complete.\", \"result\": {analysis_result}}}")
        return analysis_result

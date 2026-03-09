.PHONY: run logs state reset install lint help

# Default target
help:
	@echo ""
	@echo "AgentWill — Makefile Commands"
	@echo "────────────────────────────────────────"
	@echo "  make run      Start Will autonomously"
	@echo "  make logs     Tail Will's live log feed"
	@echo "  make state    Print current state.json"
	@echo "  make reset    Reset state.json to defaults"
	@echo "  make install  Install all dependencies"
	@echo "  make lint     Run pyflakes syntax check"
	@echo "────────────────────────────────────────"
	@echo ""

# Start Will
run:
	@echo "Starting AgentWill..."
	python agent_will.py

# Tail live logs
logs:
	@echo "Tailing Will's log..."
	tail -f logs/agent_will.log

# Print current state
state:
	@echo ""
	@cat state.json
	@echo ""

# Reset state.json to defaults
reset:
	@echo "Resetting state.json to defaults..."
	@python -c "import json; open('state.json','w').write(json.dumps({'phase':'Initialization','current_objective_index':0,'action_queue':[],'mrr_history':[],'exit_prep_triggered':False,'selected_niche':None,'last_research':{},'business_listed':None,'business_sold':None,'exit_multiple':None,'sale_price':None,'milestones':{'first_dollar':None,'mrr_100':None,'mrr_1k':None,'mrr_5k':None,'mrr_20k':None,'mrr_50k':None,'business_listed':None,'business_sold':None}},indent=4))"
	@echo "state.json reset. Will start fresh on next run."

# Install dependencies
install:
	@echo "Installing dependencies..."
	pip install -r requirements.txt

# Lint all Python files
lint:
	@echo "Running pyflakes..."
	pyflakes agent_will.py config.py tools/*.py

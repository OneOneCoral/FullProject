# agents/core/agent_registry.py
from typing import Dict, Tuple
from Projects.PygameProject.Agent.agent_list.suport_functions.agent_utils import module_exists

def get_agents() -> Dict[str, str]:
    return {
        "scanner": "agents.PromtAgents.20251220_scanner_agent",
        "test_prompt": "agents.PromtAgents.20251220_test_prompt_agent",
        "create_file_test": "agents.NonPromtAgents.create_file_test",
    }

def validate_agents(
    agent_map: Dict[str, str],
) -> Tuple[Dict[str, str], Dict[str, str]]:
    valid = {}
    missing = {}

    for name, module in agent_map.items():
        if module_exists(module):
            valid[name] = module
        else:
            missing[name] = module

    return valid, missing

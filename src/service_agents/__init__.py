"""
Service agents module for the application.

This module provides the agents that are used in the application.
"""

from .orchestrator_agent import getOrchestratorAgent
from .planning_agent import getPlanningAgent
from .coding_agent import getCodingAgent
from .testing_agent import getTestingAgent
from .evaluation_agent import getEvaluatorAgent
from .llm_context_management_agent import getLLMContextManagementAgent

__all__ = [
    'getOrchestratorAgent',
    'getPlanningAgent',
    'getCodingAgent',
    'getTestingAgent',
    'getEvaluatorAgent',
    'getLLMContextManagementAgent'
]


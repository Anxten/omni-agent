"""
Base Specialist Agent Class
Provides template and interface for all specialized sub-agents.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class AgentConfig:
    """Configuration for a specialist agent."""
    name: str
    job_description: str
    system_prompt: str
    capabilities: list[str]


class SpecialistAgent(ABC):
    """
    Abstract base class for specialist sub-agents.
    Each agent has its own system prompt, job description, and execution logic.
    """

    def __init__(self, config: AgentConfig):
        """
        Initialize specialist agent with configuration.
        
        Args:
            config: AgentConfig containing name, description, and system prompt.
        """
        self.config = config
        self.name = config.name
        self.job_description = config.job_description
        self.system_prompt = config.system_prompt
        self.capabilities = config.capabilities

    @abstractmethod
    def execute(self, goal: str, context: str, **kwargs) -> Dict[str, Any]:
        """
        Execute the specialist agent's task.
        
        Args:
            goal: The user's objective/query.
            context: The code/file context from local repository.
            **kwargs: Optional parameters specific to the agent.
            
        Returns:
            Dictionary containing the execution result.
        """
        pass

    def can_handle(self, goal: str) -> tuple[bool, float]:
        """
        Determine if this agent can handle the given goal.
        Returns (can_handle, confidence_score).
        
        Args:
            goal: The user's objective/query.
            
        Returns:
            Tuple of (can_handle: bool, confidence: float [0-1]).
        """
        # Default implementation - override in subclasses
        goal_lower = goal.lower()
        matching_capabilities = sum(
            1 for cap in self.capabilities 
            if cap.lower() in goal_lower
        )
        confidence = min(matching_capabilities / len(self.capabilities), 1.0) if self.capabilities else 0.0
        return matching_capabilities > 0, confidence

    def get_info(self) -> Dict[str, Any]:
        """Get agent information for routing/discovery."""
        return {
            "name": self.name,
            "job_description": self.job_description,
            "capabilities": self.capabilities,
            "system_prompt_preview": self.system_prompt[:200] + "..." if len(self.system_prompt) > 200 else self.system_prompt,
        }

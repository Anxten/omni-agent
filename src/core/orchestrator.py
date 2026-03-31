"""
Agent Orchestrator
Central router that manages multiple specialist agents and routes goals intelligently.
"""

from typing import Dict, Any, Optional, List
from src.agents.base_agent import SpecialistAgent
from src.agents.security_agent import SecurityAuditAgent
from src.agents.docs_agent import DocumentationAgent
from src.agents.codegen_agent import CodeGeneratorAgent
from src.agents.academic_agent import AcademicAgent
from src.agents.sales_agent import SalesAgent


class AgentOrchestrator:
    """
    Central orchestrator platform that manages multiple specialist agents.
    Routes user goals to the most appropriate specialist based on capability matching.
    """

    def __init__(self):
        """Initialize orchestrator with all available specialist agents."""
        self.agents: List[SpecialistAgent] = [
            SecurityAuditAgent(),
            DocumentationAgent(),
            CodeGeneratorAgent(),
            AcademicAgent(),
            SalesAgent(),
        ]
        self.goal_history: List[Dict[str, Any]] = []

    def register_agent(self, agent: SpecialistAgent) -> None:
        """
        Register a new specialist agent with the orchestrator.
        
        Args:
            agent: SpecialistAgent instance to register.
        """
        if agent not in self.agents:
            self.agents.append(agent)

    def find_best_agent(self, goal: str) -> Optional[SpecialistAgent]:
        """
        Intelligently route goal to the best specialist agent.
        Uses capability matching and confidence scoring.
        
        Args:
            goal: The user's objective/query.
            
        Returns:
            Best matching SpecialistAgent or None if no suitable agent found.
        """
        candidates = []
        
        for agent in self.agents:
            can_handle, confidence = agent.can_handle(goal)
            if can_handle:
                candidates.append((agent, confidence))
        
        if not candidates:
            return None
        
        # Sort by confidence score and return the best match
        best_agent, best_score = sorted(candidates, key=lambda x: x[1], reverse=True)[0]
        return best_agent

    def route_goal(
        self, 
        goal: str, 
        context: str,
        force_agent: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Route goal to appropriate specialist agent and execute.
        
        Args:
            goal: The user's objective/query.
            context: Code/file context from repository.
            force_agent: Optional agent name to force routing to specific agent.
            **kwargs: Additional parameters to pass to agent.
            
        Returns:
            Dictionary with execution result and metadata.
        """
        # Find target agent
        if force_agent:
            agent = self._find_agent_by_name(force_agent)
            if not agent:
                return {
                    "status": "error",
                    "error": f"Agent '{force_agent}' not found",
                    "available_agents": [a.name for a in self.agents],
                }
        else:
            agent = self.find_best_agent(goal)
        
        if not agent:
            return {
                "status": "error",
                "error": "No suitable agent found for this goal",
                "hint": "Try specifying the agent type more clearly or use --list-agents",
                "available_agents": self.get_available_agents(),
            }
        
        # Execute through selected agent
        result = agent.execute(goal, context, **kwargs)
        
        # Log to history
        self.goal_history.append({
            "goal": goal,
            "agent": agent.name,
            "status": result.get("status"),
        })
        
        return result

    def list_agents(self) -> List[Dict[str, Any]]:
        """
        List all available specialist agents with their information.
        
        Returns:
            List of agent information dictionaries.
        """
        return [agent.get_info() for agent in self.agents]

    def get_available_agents(self) -> List[str]:
        """
        Get list of available agent names.
        
        Returns:
            List of agent names.
        """
        return [agent.name for agent in self.agents]

    def _find_agent_by_name(self, agent_name: str) -> Optional[SpecialistAgent]:
        """
        Find agent by name (case-insensitive).
        
        Args:
            agent_name: Name of the agent to find.
            
        Returns:
            SpecialistAgent instance or None.
        """
        name_lower = agent_name.lower()
        for agent in self.agents:
            if agent.name.lower() == name_lower or name_lower in agent.name.lower():
                return agent
        return None

    def get_agent_details(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific agent.
        
        Args:
            agent_name: Name of the agent.
            
        Returns:
            Agent information dictionary or None.
        """
        agent = self._find_agent_by_name(agent_name)
        if agent:
            return {
                **agent.get_info(),
                "system_prompt": agent.system_prompt,
            }
        return None

    def get_execution_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get history of executed goals.
        
        Args:
            limit: Maximum number of history entries to return.
            
        Returns:
            List of execution history entries.
        """
        return self.goal_history[-limit:]

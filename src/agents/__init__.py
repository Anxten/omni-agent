"""
Specialist Agents Module
Dynamic agent routing with specialized system prompts and job descriptions.
"""

from src.agents.base_agent import SpecialistAgent
from src.agents.security_agent import SecurityAuditAgent
from src.agents.docs_agent import DocumentationAgent
from src.agents.codegen_agent import CodeGeneratorAgent

__all__ = [
    "SpecialistAgent",
    "SecurityAuditAgent",
    "DocumentationAgent",
    "CodeGeneratorAgent",
]

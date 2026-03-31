"""
Specialist Agents Module
Dynamic agent routing with specialized system prompts and job descriptions.
"""

from src.agents.base_agent import SpecialistAgent
from src.agents.security_agent import SecurityAuditAgent
from src.agents.docs_agent import DocumentationAgent
from src.agents.codegen_agent import CodeGeneratorAgent
from src.agents.academic_agent import AcademicAgent
from src.agents.sales_agent import SalesAgent
from src.agents.finance_agent import FinanceAgent

__all__ = [
    "SpecialistAgent",
    "SecurityAuditAgent",
    "DocumentationAgent",
    "CodeGeneratorAgent",
    "AcademicAgent",
    "SalesAgent",
    "FinanceAgent",
]

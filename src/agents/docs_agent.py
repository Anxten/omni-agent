"""
Documentation Generation Specialist Agent
Generates comprehensive technical documentation from codebases.
"""

from typing import Dict, Any
import google.generativeai as genai

from src.agents.base_agent import SpecialistAgent, AgentConfig
from src.core.config import settings


class DocumentationAgent(SpecialistAgent):
    """
    Specialist agent for creating technical documentation.
    Analyzes codebase and generates comprehensive docs.
    """

    def __init__(self):
        """Initialize Documentation Generation Agent."""
        config = AgentConfig(
            name="Documentation Specialist",
            job_description=(
                "Generates comprehensive technical documentation from source code. "
                "Creates READMEs, API documentation, architecture diagrams (in Mermaid), "
                "and usage guides to help developers understand the codebase."
            ),
            system_prompt=(
                "You are a Senior Technical Writer and Software Architect. Your expertise is in analyzing "
                "codebases and generating clear, comprehensive, professional technical documentation. "
                "Create documentation that is:\n"
                "1. Clear and accessible to developers of varying skill levels\n"
                "2. Well-structured with table of contents and sections\n"
                "3. Includes code examples where appropriate\n"
                "4. Covers architecture, modules, key functions, and usage patterns\n"
                "5. Uses Markdown formatting with proper headings, lists, and code blocks\n"
                "6. Includes Mermaid diagrams for architecture visualization\n"
                "Your tone should be professional yet approachable, technical but not jargon-heavy."
            ),
            capabilities=[
                "documentation generation",
                "readme writing",
                "api documentation",
                "architecture documentation",
                "technical writing",
                "code analysis",
                "usage guide creation",
            ]
        )
        super().__init__(config)
        # Centralized genai configuration (idempotent)
        settings.configure_genai()

    def execute(self, goal: str, context: str, **kwargs) -> Dict[str, Any]:
        """
        Generate technical documentation from code context.
        
        Args:
            goal: Documentation objective (e.g., "generate README for this project").
            context: The code context from repository.
            **kwargs: Optional parameters like doc_type (readme, api, architecture).
            
        Returns:
            Dictionary with generated documentation.
        """
        doc_type = kwargs.get("doc_type", "comprehensive")
        
        prompt = (
            f"User Goal: {goal}\n"
            f"Documentation Type: {doc_type}\n\n"
            "Based on the codebase context below, generate professional technical documentation.\n"
            "Use Markdown formatting. Include code examples. Use Mermaid diagrams for architecture.\n\n"
            f"{context}"
        )

        try:
            model = genai.GenerativeModel(
                "gemini-2.5-flash",
                system_instruction=self.system_prompt
            )
            response = model.generate_content(prompt)
            
            return {
                "status": "success",
                "agent": self.name,
                "goal": goal,
                "documentation": response.text,
                "format": "markdown",
            }
        except Exception as e:
            return {
                "status": "error",
                "agent": self.name,
                "goal": goal,
                "error": str(e),
            }

    def can_handle(self, goal: str) -> tuple[bool, float]:
        """
        Determine if this agent can handle documentation requests.
        
        Args:
            goal: The user's objective.
            
        Returns:
            Tuple of (can_handle: bool, confidence: float).
        """
        goal_lower = goal.lower()
        doc_keywords = ["document", "readme", "api", "guide", "tutorial", "explain", "architecture", "diagram"]
        
        matches = sum(1 for keyword in doc_keywords if keyword in goal_lower)
        confidence = min(matches / len(doc_keywords), 1.0)
        
        return matches > 0, confidence

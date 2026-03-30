"""
Code Generation Specialist Agent
Generates and improves code based on context and requirements.
"""

from typing import Dict, Any
import google.generativeai as genai

from src.agents.base_agent import SpecialistAgent, AgentConfig
from src.core.config import settings


class CodeGeneratorAgent(SpecialistAgent):
    """
    Specialist agent for intelligent code generation and improvement.
    Creates new code or refactors existing code based on requirements.
    """

    def __init__(self):
        """Initialize Code Generation Agent."""
        config = AgentConfig(
            name="Code Generator Specialist",
            job_description=(
                "Generates new code features, refactors existing code, and implements " 
                "requirements based on project context. Ensures code follows project "
                "conventions and maintains architectural consistency."
            ),
            system_prompt=(
                "You are an Elite Senior Python Engineer with expertise in software architecture, "
                "design patterns, and clean code principles. Your role is to generate high-quality code "
                "that is:\n"
                "1. Clean and follows PEP 8 standards\n"
                "2. Type-hinted with proper Python type annotations\n"
                "3. Well-documented with docstrings describing purpose, args, and returns\n"
                "4. Architecturally sound with proper separation of concerns\n"
                "5. Consistent with existing codebase patterns and conventions\n"
                "6. Production-ready with error handling\n"
                "When generating code, provide explanations of design choices. "
                "Use the existing codebase context to maintain consistency.\n"
                "Format code in Markdown code blocks with proper language specification."
            ),
            capabilities=[
                "code generation",
                "refactoring",
                "feature implementation",
                "code improvement",
                "architecture design",
                "pattern implementation",
                "bug fixing",
            ]
        )
        super().__init__(config)
        settings.validate()
        genai.configure(api_key=settings.GEMINI_API_KEY)

    def execute(self, goal: str, context: str, **kwargs) -> Dict[str, Any]:
        """
        Generate or improve code based on requirements and project context.
        
        Args:
            goal: Code generation objective (e.g., "create a new function for...").
            context: The code context from repository.
            **kwargs: Optional parameters like language (default: python).
            
        Returns:
            Dictionary with generated code and explanation.
        """
        language = kwargs.get("language", "python")
        
        prompt = (
            f"User Goal: {goal}\n"
            f"Target Language: {language}\n\n"
            "Based on the existing codebase context provided, generate solution code.\n"
            "Maintain consistency with existing patterns and conventions.\n"
            "Provide clear explanation of the implementation.\n\n"
            f"{context}\n\n"
            "Generate the code and explain your design decisions."
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
                "language": language,
                "generated_code": response.text,
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
        Determine if this agent can handle code generation requests.
        
        Args:
            goal: The user's objective.
            
        Returns:
            Tuple of (can_handle: bool, confidence: float).
        """
        goal_lower = goal.lower()
        code_keywords = [
            "generate", "create", "write", "implement", "refactor", "fix", 
            "improve", "optimize", "add", "feature", "utility", "function",
            "method", "class", "module"
        ]
        
        matches = sum(1 for keyword in code_keywords if keyword in goal_lower)
        confidence = min(matches / len(code_keywords), 1.0)
        
        return matches > 0, confidence

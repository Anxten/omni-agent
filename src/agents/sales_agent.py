"""
B2B Sales Closer Specialist Agent
Generates high-converting outreach copy from security audit reports.
"""

import os
from typing import Dict, Any

import google.generativeai as genai

from src.agents.base_agent import SpecialistAgent, AgentConfig
from src.core.config import settings
from src.utils.file_reader import read_codebase_for_audit_single_batch


class SalesAgent(SpecialistAgent):
    """Specialist agent for B2B cybersecurity outreach and conversion copy."""

    def __init__(self):
        """Initialize B2B Sales Closer agent."""
        config = AgentConfig(
            name="B2B Sales Closer",
            job_description=(
                "Reads technical security reports and generates high-converting "
                "executive outreach copy for cybersecurity sales."
            ),
            system_prompt=(
                "You are an elite B2B cybersecurity sales closer. Your job is to read a technical "
                "security audit report and generate: 1. A highly converting, short Cold Email to "
                "the CTO/CEO highlighting the financial risk of the found vulnerabilities. 2. A "
                "concise, punchy LinkedIn DM. Use psychological leverage and professional tone. "
                "NEVER hallucinate vulnerabilities; only use what is in the report."
            ),
            capabilities=["pitch", "email", "sales", "outreach", "cold dm"],
        )
        super().__init__(config)
        settings.validate()
        genai.configure(api_key=settings.GEMINI_API_KEY)

    def execute(self, goal: str, context: str, **kwargs) -> Dict[str, Any]:
        """
        Read report context and generate sales outreach pitch in one Gemini call.

        Args:
            goal: User objective for sales copy generation.
            context: Pre-aggregated context if provided by caller.
            **kwargs: Optional context_path for direct report reading.

        Returns:
            Dictionary containing generated pitch content.
        """
        context_path = kwargs.get("context_path")
        combined_context = context

        if isinstance(context_path, str) and os.path.exists(context_path):
            if os.path.isfile(context_path):
                report_context = self._read_report_file(context_path)
            else:
                report_context = read_codebase_for_audit_single_batch(context_path)

            if report_context.startswith("[System Error:"):
                return {
                    "status": "error",
                    "agent": self.name,
                    "goal": goal,
                    "error": report_context,
                }

            combined_context = report_context

        prompt = (
            f"User Goal: {goal}\n\n"
            "Generate the requested outreach copy from this security report context.\n\n"
            f"{combined_context}"
        )

        try:
            model = genai.GenerativeModel("gemini-2.5-flash", system_instruction=self.system_prompt)
            response = model.generate_content(prompt)
            return {
                "status": "success",
                "agent": self.name,
                "goal": goal,
                "pitch": response.text,
            }
        except Exception as e:
            return {
                "status": "error",
                "agent": self.name,
                "goal": goal,
                "error": str(e),
            }

    def can_handle(self, goal: str) -> tuple[bool, float]:
        """Determine if this agent should handle a sales outreach task."""
        goal_lower = goal.lower()
        matches = sum(1 for keyword in self.capabilities if keyword in goal_lower)
        confidence = min(matches / len(self.capabilities), 1.0)
        return matches > 0, confidence

    def _read_report_file(self, file_path: str) -> str:
        """Read a report file robustly and wrap it with clear boundaries."""
        encodings = ("utf-8", "utf-8-sig", "latin-1")
        last_error: Exception | None = None

        for encoding in encodings:
            try:
                with open(file_path, "r", encoding=encoding) as file:
                    content = file.read()
                return (
                    f"--- START REPORT: {os.path.basename(file_path)} ---\n"
                    f"{content}\n"
                    "--- END REPORT ---"
                )
            except Exception as exc:
                last_error = exc

        return f"[System Error: Failed to read report file '{file_path}': {str(last_error)}]"

"""
DeFi Financial Analyst Specialist Agent
Generates investment thesis reports from whitepapers and tokenomics documents.
"""

import os
from typing import Dict, Any

import google.generativeai as genai

from src.agents.base_agent import SpecialistAgent, AgentConfig
from src.core.config import settings
from src.utils.file_reader import read_codebase_for_audit_single_batch


class FinanceAgent(SpecialistAgent):
    """Specialist agent for DeFi/Crypto financial and tokenomics analysis."""

    def __init__(self):
        """Initialize DeFi Financial Analyst agent."""
        config = AgentConfig(
            name="DeFi Financial Analyst",
            job_description=(
                "Analyzes DeFi/Crypto whitepapers, tokenomics documents, and financial reports "
                "to produce a structured investment thesis and risk verdict."
            ),
            system_prompt=(
                "You are a ruthless, pragmatic DeFi/Crypto financial analyst and wealth strategist. "
                "Your job is to ingest the provided whitepaper, tokenomics document, or financial report. "
                "Output a highly structured markdown report containing: "
                "1. Core Value Proposition (What do they actually do?). "
                "2. Red Flags / Ponzi Mechanics (Identify unsustainable yields or token dumps). "
                "3. Smart Contract Audit Viability (Is this a high-value, high-risk target that desperately needs our security audit services?). "
                "4. Final Verdict (Bullish / Bearish / Scam / High-Priority Audit Target). "
                "Be brutal and precise. "
                "STRICT VERDICT RULES: "
                "A) The Final Verdict must be exactly one label from this set: Bullish, Bearish, Scam, High-Priority Audit Target. "
                "B) You are forbidden from soft or defensive verdicts such as 'not applicable', 'unclear', 'mixed', or 'depends'. "
                "C) You must commit to one label based on available evidence and explain why in 1-3 concise bullet points."
            ),
            capabilities=["finance", "tokenomics", "whitepaper", "invest", "crypto", "defi"],
        )
        super().__init__(config)
        settings.validate()
        genai.configure(api_key=settings.GEMINI_API_KEY)

    def execute(self, goal: str, context: str, **kwargs) -> Dict[str, Any]:
        """
        Read financial context and generate a markdown investment thesis in one Gemini call.

        Args:
            goal: User objective for financial analysis.
            context: Pre-aggregated context if provided by caller.
            **kwargs: Optional context_path for direct file/directory reading.

        Returns:
            Dictionary containing generated markdown thesis.
        """
        context_path = kwargs.get("context_path")
        combined_context = context

        if isinstance(context_path, str) and os.path.exists(context_path):
            batched_context = read_codebase_for_audit_single_batch(context_path)
            if batched_context.startswith("[System Error:"):
                return {
                    "status": "error",
                    "agent": self.name,
                    "goal": goal,
                    "error": batched_context,
                }
            combined_context = batched_context

        prompt = (
            f"User Goal: {goal}\n\n"
            "Analyze this DeFi/Crypto material and produce the requested structured markdown report.\n\n"
            f"{combined_context}"
        )

        try:
            model = genai.GenerativeModel("gemini-2.5-flash", system_instruction=self.system_prompt)
            response = model.generate_content(prompt)
            return {
                "status": "success",
                "agent": self.name,
                "goal": goal,
                "markdown": response.text,
            }
        except Exception as e:
            return {
                "status": "error",
                "agent": self.name,
                "goal": goal,
                "error": str(e),
            }

    def can_handle(self, goal: str) -> tuple[bool, float]:
        """Determine if this agent should handle a finance/tokenomics request."""
        goal_lower = goal.lower()
        matches = sum(1 for keyword in self.capabilities if keyword in goal_lower)
        confidence = min(matches / len(self.capabilities), 1.0)
        return matches > 0, confidence

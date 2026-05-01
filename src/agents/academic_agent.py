"""
Academic Strategist Specialist Agent
Analyzes study materials to produce high-yield study guides.
"""

import os
from typing import Dict, Any

import google.generativeai as genai

from src.agents.base_agent import SpecialistAgent, AgentConfig
from src.core.config import settings
from src.utils.file_reader import read_codebase_for_audit_single_batch, IGNORED_DIRS

try:
    from pypdf import PdfReader
except Exception:
    PdfReader = None


class AcademicAgent(SpecialistAgent):
    """Specialist agent for academic study strategy and exam preparation."""

    def __init__(self):
        """Initialize Academic Strategist agent."""
        config = AgentConfig(
            name="Academic Strategist",
            job_description=(
                "Analyzes study materials, university PDFs, and lecture notes to "
                "generate high-yield study guides."
            ),
            system_prompt=(
                "You are an elite academic strategist for an Informatics student. "
                "Your job is to ingest study materials and output: "
                "1. A highly condensed executive summary of core concepts. "
                "2. 5 Key Flashcards (Term: Definition). "
                "3. 3 High-probability exam questions with answers. "
                "Format the output in clean Markdown."
            ),
            capabilities=["study", "summarize", "flashcards", "exam prep", "academic"],
        )
        super().__init__(config)
        # Centralized genai configuration (idempotent)
        settings.configure_genai()

    def execute(self, goal: str, context: str, **kwargs) -> Dict[str, Any]:
        """
        Ingest study materials as one combined context and generate Markdown output.

        The method uses single-shot batching and sends one Gemini request.
        """
        context_path = kwargs.get("context_path")
        resolved_path = context_path or context

        # If caller passes a real path, build a single large context from files.
        if isinstance(resolved_path, str) and os.path.exists(resolved_path):
            batched_context = read_codebase_for_audit_single_batch(resolved_path)
            pdf_context = self._read_pdf_materials(resolved_path)

            if batched_context.startswith("[System Error:") and not pdf_context:
                return {
                    "status": "error",
                    "agent": self.name,
                    "goal": goal,
                    "error": batched_context,
                }

            combined_context = "\n\n".join(part for part in [batched_context, pdf_context] if part)
        else:
            # Fallback for current orchestrator flow where context is already pre-aggregated.
            combined_context = context

        prompt = (
            f"User Goal: {goal}\n\n"
            "Generate an academic study guide from the materials below.\n\n"
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
        """Determine if this agent should handle an academic study request."""
        goal_lower = goal.lower()
        matches = sum(1 for keyword in self.capabilities if keyword in goal_lower)
        confidence = min(matches / len(self.capabilities), 1.0)
        return matches > 0, confidence

    def _read_pdf_materials(self, path: str) -> str:
        """Extract text from PDF files and append to the combined context."""
        if PdfReader is None:
            return ""

        normalized_path = os.path.abspath(path)
        pdf_files: list[str] = []

        if os.path.isfile(normalized_path) and normalized_path.lower().endswith(".pdf"):
            pdf_files.append(normalized_path)
        elif os.path.isdir(normalized_path):
            for root, dirs, files in os.walk(normalized_path):
                dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
                for filename in files:
                    if filename.lower().endswith(".pdf"):
                        pdf_files.append(os.path.join(root, filename))

        if not pdf_files:
            return ""

        parts = [f"--- START PDF MATERIALS: {normalized_path} ---"]
        for pdf_path in sorted(pdf_files):
            try:
                reader = PdfReader(pdf_path)
                pages: list[str] = []
                for page in reader.pages:
                    page_text = page.extract_text() or ""
                    if page_text.strip():
                        pages.append(page_text)

                display_path = os.path.relpath(pdf_path, start=normalized_path) if os.path.isdir(normalized_path) else os.path.basename(pdf_path)
                parts.append(f"--- START PDF: {display_path} ---")
                parts.append("\n".join(pages) if pages else "[Warning: No extractable text found]")
                parts.append("--- END PDF ---")
            except Exception as exc:
                parts.append(f"--- START PDF: {os.path.basename(pdf_path)} ---")
                parts.append(f"[Warning: Failed to parse PDF: {str(exc)}]")
                parts.append("--- END PDF ---")

        parts.append("--- END PDF MATERIALS ---")
        return "\n\n".join(parts)

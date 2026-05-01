"""
Security Audit Specialist Agent
Performs automated SAST (Static Application Security Testing) on codebase.
"""

import json
from typing import Dict, Any
import google.generativeai as genai

from src.agents.base_agent import SpecialistAgent, AgentConfig
from src.core.config import settings


class SecurityAuditAgent(SpecialistAgent):
    """
    Specialist agent for security vulnerability detection.
    Uses OWASP Top 10 compliance framework.
    """

    def __init__(self):
        """Initialize Security Audit Agent with SAST configuration."""
        config = AgentConfig(
            name="Security Audit Specialist",
            job_description=(
                "Performs automated Static Application Security Testing (SAST) "
                "on source code to identify vulnerabilities, security flaws, and "
                "compliance issues aligned with OWASP Top 10 framework."
            ),
            system_prompt=(
                "You are an Elite DevSecOps and Application Security Engineer. Your objective is to perform a brutal, "
                "uncompromising Static Application Security Testing (SAST) on the provided codebase. "
                "Your methodology is strictly based on the OWASP Top 10 vulnerabilities (e.g., SQL Injection, XSS, "
                "Broken Access Control, Hardcoded Secrets, Insecure Direct Object References). "
                "Apply these Web3 Security heuristics carefully: Soroban TTL is paid by the caller, and a public TTL "
                "extension is a feature used to prevent deletion rather than a DoS bug. Also, Rust generic or helper "
                "functions may be protected by wrapping macros such as #[lz_contract] constructors, so do not flag them "
                "as Broken Access Control unless they are directly exposed as public entrypoints. "
                "Analyze the provided code and identify ANY security vulnerabilities, bad practices, or potential attack vectors. "
                "CRITICAL RULE: You MUST return the output EXCLUSIVELY in valid JSON format. "
                "Do not include markdown formatting, conversational text, or explanations outside the JSON structure. "
                "IMPORTANT FORMATTING RULES FOR JSON VALUES: "
                "1. The 'remediation_code' field must contain a plain English description of the fix. Do NOT include actual code, backticks, triple backticks, or code fences inside any JSON string value. "
                "2. Do NOT use backtick characters (`) anywhere in the JSON output. "
                "3. All string values in the JSON must be simple plain text, properly escaped. "
                "JSON STRUCTURE: "
                "{"
                "\"audit_summary\": {"
                "\"total_vulnerabilities\": <int>,"
                "\"critical_count\": <int>,"
                "\"high_count\": <int>,"
                "\"medium_count\": <int>,"
                "\"low_count\": <int>"
                "},"
                "\"findings\": ["
                "{"
                "\"severity\": \"<CRITICAL|HIGH|MEDIUM|LOW>\","
                "\"vulnerability_type\": \"<e.g., SQL Injection, Hardcoded Secret>\","
                "\"file_path\": \"<extracted from context>\","
                "\"line_number_or_function\": \"<approximate location>\","
                "\"description\": \"<Clear explanation of HOW the attack can be executed>\","
                "\"remediation_code\": \"<The exact code snippet to fix the issue>\""
                "}"
                "]"
                "}"
            ),
            capabilities=[
                "security audit",
                "vulnerability detection",
                "sast",
                "code inspection",
                "owasp",
                "vulnerability assessment",
                "security analysis",
                "code review",
            ]
        )
        super().__init__(config)
        # Centralized genai configuration (idempotent)
        settings.configure_genai()

    def execute(self, goal: str, context: str, **kwargs) -> Dict[str, Any]:
        """
        Execute SAST analysis on provided code context.
        
        Args:
            goal: User's security audit objective (e.g., "audit for vulnerabilities").
            context: The code context from repository (from single-shot batching).
            **kwargs: Optional parameters (unused for SAST).
            
        Returns:
            Dictionary with parsed audit results or error message.
        """
        prompt = (
            f"User Goal: {goal}\n\n"
            "Perform SAST analysis on this codebase context and return only valid JSON.\n\n"
            f"{context}"
        )

        try:
            model = genai.GenerativeModel(
                "gemini-2.5-flash",
                system_instruction=self.system_prompt
            )
            response = model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            raw_text = response.text

            # Parse JSON response with fallback extraction
            parsed = self._extract_json_payload(raw_text)
            return {
                "status": "success",
                "agent": self.name,
                "goal": goal,
                "result": parsed,
                "raw_response": raw_text,
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
        Override: Determine if this agent can handle security-related goals.
        
        Args:
            goal: The user's objective.
            
        Returns:
            Tuple of (can_handle: bool, confidence: float).
        """
        goal_lower = goal.lower()
        security_keywords = ["audit", "security", "vulnerability", "sast", "scan", "inspect", "review", "flaw"]
        
        matches = sum(1 for keyword in security_keywords if keyword in goal_lower)
        confidence = min(matches / len(security_keywords), 1.0)
        
        return matches > 0, confidence

    def _extract_json_payload(self, raw_text: str) -> dict:
        """
        Parse JSON with fallback extraction for robust response handling.
        
        Args:
            raw_text: Raw response text from LLM.
            
        Returns:
            Parsed JSON dictionary.
        """
        stripped = raw_text.strip()

        # Remove markdown code blocks if present
        if stripped.startswith("```"):
            lines = stripped.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            stripped = "\n".join(lines).strip()

        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            # Fallback: extract largest JSON object
            start_index = stripped.find("{")
            if start_index == -1:
                raise ValueError("No JSON object found in response")
            
            candidate = stripped[start_index:]
            decoder = json.JSONDecoder()
            parsed, _ = decoder.raw_decode(candidate)
            return parsed

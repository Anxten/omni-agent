# Building Custom Specialist Agents

This guide shows how to create and register new specialist agents to extend Omni Agent's capabilities.

## Quick Overview

### 1. Create Agent Class
Inherit from `SpecialistAgent` and implement required methods.

### 2. Define System Prompt
Specify how the agent should behave (LLM persona and constraints).

### 3. Register with Orchestrator
Add agent to the orchestrator's agent list.

## Example 1: Performance Optimizer Agent

Let's create an agent that analyzes code for performance issues.

### Step 1: Create the Agent File

Create `src/agents/performance_agent.py`:

```python
"""
Performance Optimization Specialist Agent
Analyzes code for performance issues and optimization opportunities.
"""

from typing import Dict, Any
import google.generativeai as genai

from src.agents.base_agent import SpecialistAgent, AgentConfig
from src.core.config import settings


class PerformanceOptimizerAgent(SpecialistAgent):
    """
    Specialist agent for performance analysis and optimization recommendations.
    Identifies bottlenecks, optimization opportunities, and best practices.
    """

    def __init__(self):
        """Initialize Performance Optimizer Agent."""
        config = AgentConfig(
            name="Performance Optimizer Specialist",
            job_description=(
                "Analyzes code for performance bottlenecks, inefficiencies, and optimization "
                "opportunities. Provides recommendations for improving execution speed, memory "
                "usage, and resource efficiency."
            ),
            system_prompt=(
                "You are a Performance Engineering Expert and Systems Optimization Specialist. "
                "Your role is to:\n"
                "1. Identify performance bottlenecks in code\n"
                "2. Analyze algorithmic complexity (Big O notation)\n"
                "3. Detect memory leaks and inefficient resource usage\n"
                "4. Recommend optimization strategies\n"
                "5. Suggest modern best practices (async/await, caching, parallel processing)\n"
                "6. Provide specific, actionable improvements\n"
                "Format your response in Markdown with:\n"
                "- Clear problem identification\n"
                "- Root cause analysis\n"
                "- Recommended solutions with code examples\n"
                "- Expected performance improvements\n"
                "- Trade-offs and implementation considerations"
            ),
            capabilities=[
                "performance analysis",
                "optimization",
                "bottleneck detection",
                "profiling",
                "efficiency improvement",
                "resource optimization",
                "scalability assessment",
            ]
        )
        super().__init__(config)
        settings.validate()
        genai.configure(api_key=settings.GEMINI_API_KEY)

    def execute(self, goal: str, context: str, **kwargs) -> Dict[str, Any]:
        """
        Analyze code for performance issues and suggest optimizations.
        
        Args:
            goal: Performance analysis objective.
            context: Source code context.
            **kwargs: Optional parameters.
            
        Returns:
            Dictionary with analysis and recommendations.
        """
        prompt = (
            f"User Goal: {goal}\n\n"
            "Analyze the following code for performance issues and provide optimization recommendations.\n"
            "Include specific, actionable suggestions with examples.\n\n"
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
                "analysis": response.text,
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
        Determine if this agent can handle performance analysis requests.
        
        Args:
            goal: The user's objective.
            
        Returns:
            Tuple of (can_handle: bool, confidence: float).
        """
        goal_lower = goal.lower()
        perf_keywords = [
            "performance", "optimize", "optimize", "speed", "slow", 
            "fast", "efficiency", "bottleneck", "profiling", "latency"
        ]
        
        matches = sum(1 for keyword in perf_keywords if keyword in goal_lower)
        confidence = min(matches / len(perf_keywords), 1.0)
        
        return matches > 0, confidence
```

### Step 2: Register with Orchestrator

Update `src/core/orchestrator.py`:

```python
# Add import at top
from src.agents.performance_agent import PerformanceOptimizerAgent

# In __init__ method, add to agents list:
def __init__(self):
    self.agents: List[SpecialistAgent] = [
        SecurityAuditAgent(),
        DocumentationAgent(),
        CodeGeneratorAgent(),
        PerformanceOptimizerAgent(),  # Add new agent
    ]
```

### Step 3: Update Agent Exports

Update `src/agents/__init__.py`:

```python
from src.agents.performance_agent import PerformanceOptimizerAgent

__all__ = [
    "SpecialistAgent",
    "SecurityAuditAgent",
    "DocumentationAgent",
    "CodeGeneratorAgent",
    "PerformanceOptimizerAgent",  # Add here
]
```

### Step 4: Test the New Agent

```bash
# List agents (should see Performance Optimizer)
omni agents

# Get details
omni agents --name "Performance Optimizer Specialist"

# Use the agent
omni execute "Analyze this code for performance bottlenecks" --context ./src

# Force usage
omni execute "Check performance" --agent "Performance Optimizer Specialist" --context ./src
```

## Example 2: Testing & Quality Agent

Create an agent that analyzes test coverage and code quality.

### File: `src/agents/quality_agent.py`

```python
"""
Code Quality & Testing Specialist Agent
Analyzes code quality, test coverage, and recommends improvements.
"""

from typing import Dict, Any
import google.generativeai as genai

from src.agents.base_agent import SpecialistAgent, AgentConfig
from src.core.config import settings


class QualityAssuranceAgent(SpecialistAgent):
    """
    Specialist agent for code quality and testing analysis.
    """

    def __init__(self):
        """Initialize QA Agent."""
        config = AgentConfig(
            name="Quality Assurance Specialist",
            job_description=(
                "Analyzes code quality metrics, test coverage, and maintainability. "
                "Provides recommendations for improving code standards, test strategies, "
                "and overall software quality."
            ),
            system_prompt=(
                "You are a Quality Assurance and Software Engineering Expert. "
                "Evaluate code based on:\n"
                "1. Test coverage and strategy\n"
                "2. Code complexity and maintainability\n"
                "3. Code style and conventions\n"
                "4. Error handling and edge cases\n"
                "5. Documentation completeness\n"
                "6. Design patterns and best practices\n"
                "Provide a structured quality report with scores and recommendations."
            ),
            capabilities=[
                "code quality analysis",
                "test coverage assessment",
                "maintainability review",
                "code style review",
                "testing strategy",
                "quality metrics",
            ]
        )
        super().__init__(config)
        settings.validate()
        genai.configure(api_key=settings.GEMINI_API_KEY)

    def execute(self, goal: str, context: str, **kwargs) -> Dict[str, Any]:
        """
        Analyze code quality and provide recommendations.
        """
        prompt = (
            f"Objective: {goal}\n\n"
            "Perform comprehensive code quality analysis including:\n"
            "- Test coverage assessment\n"
            "- Code complexity metrics\n"
            "- Maintainability score\n"
            "- Recommendations for improvement\n\n"
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
                "quality_report": response.text,
            }
        except Exception as e:
            return {
                "status": "error",
                "agent": self.name,
                "error": str(e),
            }

    def can_handle(self, goal: str) -> tuple[bool, float]:
        """Determine if this agent can handle QA requests."""
        goal_lower = goal.lower()
        qa_keywords = [
            "quality", "test", "coverage", "maintainability", "refactor",
            "review", "standards", "best practices", "complexity"
        ]
        
        matches = sum(1 for keyword in qa_keywords if keyword in goal_lower)
        confidence = min(matches / len(qa_keywords), 1.0)
        
        return matches > 0, confidence
```

## Example 3: API Design Specialist

Create an agent that reviews and suggests API improvements.

### File: `src/agents/api_agent.py`

```python
"""
API Design Specialist Agent
Reviews API design and provides RESTful best practices recommendations.
"""

from typing import Dict, Any
import google.generativeai as genai

from src.agents.base_agent import SpecialistAgent, AgentConfig
from src.core.config import settings


class APIDesignAgent(SpecialistAgent):
    """Specialist for API design review and recommendations."""

    def __init__(self):
        """Initialize API Design Agent."""
        config = AgentConfig(
            name="API Design Specialist",
            job_description=(
                "Reviews API design for REST best practices, consistency, and usability. "
                "Provides recommendations for better API structure, versioning, error handling, "
                "and developer experience."
            ),
            system_prompt=(
                "You are an API Architecture and Design Expert. Review APIs based on:\n"
                "1. REST principles and conventions\n"
                "2. Resource modeling\n"
                "3. Versioning strategy\n"
                "4. Error handling and status codes\n"
                "5. Security best practices\n"
                "6. Documentation and discoverability\n"
                "7. Performance and caching strategies\n"
                "Provide actionable recommendations with examples."
            ),
            capabilities=[
                "api design review",
                "rest api audit",
                "endpoint design",
                "api versioning",
                "api documentation",
                "api security",
            ]
        )
        super().__init__(config)
        settings.validate()
        genai.configure(api_key=settings.GEMINI_API_KEY)

    def execute(self, goal: str, context: str, **kwargs) -> Dict[str, Any]:
        """Analyze API design."""
        prompt = (
            f"API Review Objective: {goal}\n\n"
            "Review the API design in this code and provide:\n"
            "1. Analysis of current design\n"
            "2. Alignment with REST principles\n"
            "3. Suggestions for improvement\n"
            "4. Best practices recommendations\n\n"
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
                "api_review": response.text,
            }
        except Exception as e:
            return {
                "status": "error",
                "agent": self.name,
                "error": str(e),
            }

    def can_handle(self, goal: str) -> tuple[bool, float]:
        """Check if can handle API design requests."""
        goal_lower = goal.lower()
        api_keywords = ["api", "rest", "endpoint", "endpoint design", "request", "response"]
        
        matches = sum(1 for keyword in api_keywords if keyword in goal_lower)
        confidence = min(matches / len(api_keywords), 1.0)
        
        return matches > 0, confidence
```

## Agent Development Template

Use this template to create new agents quickly:

```python
"""
[Agent Purpose and Description]
"""

from typing import Dict, Any
import google.generativeai as genai

from src.agents.base_agent import SpecialistAgent, AgentConfig
from src.core.config import settings


class [YourAgentName](SpecialistAgent):
    """
    Specialist agent for [purpose].
    """

    def __init__(self):
        """Initialize agent."""
        config = AgentConfig(
            name="[Display Name]",
            job_description="[What this agent does]",
            system_prompt="[LLM behavior and constraints]",
            capabilities=[
                # List of capability keywords for routing
                "keyword1",
                "keyword2",
            ]
        )
        super().__init__(config)
        settings.validate()
        genai.configure(api_key=settings.GEMINI_API_KEY)

    def execute(self, goal: str, context: str, **kwargs) -> Dict[str, Any]:
        """Execute the agent's task."""
        prompt = f"Goal: {goal}\n\n{context}"

        try:
            model = genai.GenerativeModel(
                "gemini-2.5-flash",
                system_instruction=self.system_prompt
            )
            response = model.generate_content(prompt)
            
            return {
                "status": "success",
                "agent": self.name,
                "result": response.text,
            }
        except Exception as e:
            return {
                "status": "error",
                "agent": self.name,
                "error": str(e),
            }

    def can_handle(self, goal: str) -> tuple[bool, float]:
        """Determine if this agent can handle the goal."""
        goal_lower = goal.lower()
        keywords = ["keyword1", "keyword2"]  # Your keywords
        
        matches = sum(1 for kw in keywords if kw in goal_lower)
        confidence = min(matches / len(keywords), 1.0)
        
        return matches > 0, confidence
```

## Best Practices for Custom Agents

### 1. System Prompt Design

```python
# ✅ Good: Clear, constrained, actionable
system_prompt = (
    "You are a Security Expert. "
    "Analyze code for vulnerabilities. "
    "Return findings in JSON format with: severity, type, description, remediation. "
    "Focus on: SQL injection, XSS, authentication flaws."
)

# ❌ Bad: Vague, no constraints
system_prompt = "You are helpful AI. Analyze code."
```

### 2. Routing Keywords

```python
# ✅ Good: Specific, frequently used words
capabilities = ["security", "vulnerability", "sast", "scan", "audit"]

# ❌ Bad: Too generic
capabilities = ["analyze", "check", "process"]
```

### 3. Error Handling

```python
# ✅ Good: Explicit error handling and logging
try:
    response = model.generate_content(prompt)
    return {"status": "success", "result": response.text}
except Exception as e:
    return {"status": "error", "error": str(e), "agent": self.name}

# ❌ Bad: Silent failures
result = model.generate_content(prompt)
return result.text
```

### 4. Output Consistency

```python
# Always return this structure
{
    "status": "success" or "error",
    "agent": self.name,          # Agent name
    "goal": goal,                # Original goal
    ...                          # Agent-specific result
}
```

## Testing Your Agent

```bash
# Test discovery
omni agents | grep "Your Agent"

# Test agent details
omni agents --name "Your Agent Name"

# Test goal routing (should work if keywords match)
omni execute "goal with your keywords"

# Force test
omni execute "any goal" --agent "Your Agent Name" --context ./src

# Save results for inspection
omni execute "goal" --agent "Your Agent" --output agent_test.json
```

## Advanced: Multi-Output Agent

Example agent that returns structured and text output:

```python
def execute(self, goal: str, context: str, **kwargs) -> Dict[str, Any]:
    """Execute with multiple output formats."""
    try:
        # Generate analysis
        model = genai.GenerativeModel(..., system_instruction=self.system_prompt)
        response = model.generate_content(prompt)
        
        # Parse and format
        analysis = self._parse_response(response.text)
        
        return {
            "status": "success",
            "agent": self.name,
            "structured": analysis,           # Parsed data
            "markdown": response.text,        # Raw markdown
            "summary": analysis.get("summary"),
        }
    except Exception as e:
        return {"status": "error", "agent": self.name, "error": str(e)}
```

## Registering Multiple New Agents

Update `__init__` in orchestrator.py:

```python
from src.agents.performance_agent import PerformanceOptimizerAgent
from src.agents.quality_agent import QualityAssuranceAgent
from src.agents.api_agent import APIDesignAgent

def __init__(self):
    self.agents: List[SpecialistAgent] = [
        SecurityAuditAgent(),
        DocumentationAgent(),
        CodeGeneratorAgent(),
        PerformanceOptimizerAgent(),    # New
        QualityAssuranceAgent(),        # New
        APIDesignAgent(),               # New
    ]
```

## Troubleshooting Custom Agents

### Agent not being selected

**Issue**: Your agent keywords don't match the goal.

**Solution**: 
1. Check `can_handle()` method keywords
2. Test with more specific goals
3. Use `--agent "Your Agent"` to force it

### Agent fails with API error

**Issue**: Gemini API error or context too large.

**Solution**:
1. Check `GEMINI_API_KEY` in .env
2. Reduce context size (use smaller path: `./src/module`)
3. Check API quota at console.cloud.google.com

### Agent output format wrong

**Issue**: Output doesn't match expected structure.

**Solution**: Update agent's `system_prompt` to include format constraints.

## What's Next?

1. Create your first custom agent (use template above)
2. Register it with orchestrator
3. Test with `omni agents`
4. Use with `omni execute --agent "Your Agent"`
5. Share your agents with the community!

---

**Remember:** A good specialist agent should:
- ✅ Have clear, specific capabilities
- ✅ Include detailed system prompts
- ✅ Return consistent output formats
- ✅ Handle errors gracefully
- ✅ Have well-chosen routing keywords

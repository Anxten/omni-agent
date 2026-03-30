# Omni Agent Orchestrator Architecture

## Overview

Omni Agent has been refactored from a single-purpose CLI auditor into a **multi-agent orchestrator platform**. The system intelligently routes user goals to specialized sub-agents, each with their own system prompts, capabilities, and execution logic.

## Architecture Components

### 1. **Base Specialist Agent** (`src/agents/base_agent.py`)

Abstract base class that all specialist agents inherit from.

```python
class SpecialistAgent(ABC):
    - config: AgentConfig          # Agent metadata
    - execute()                     # Abstract execution method
    - can_handle()                  # Capability routing
    - get_info()                    # Agent discovery
```

**Key Features:**
- Each agent has a unique `system_prompt` for LLM behavior
- `capabilities` list for intelligent goal routing
- `can_handle()` method returns (bool, confidence_score) for routing decisions
- standardized execution interface

### 2. **Specialist Agents**

#### A. Security Audit Agent (`src/agents/security_agent.py`)
- **Job**: Performs SAST (Static Application Security Testing)
- **Framework**: OWASP Top 10 compliance
- **Output**: JSON-formatted vulnerability findings
- **Capabilities**: `security audit`, `vulnerability detection`, `sast`, `code inspection`, `owasp`

```bash
omni execute "Audit this codebase for vulnerabilities" --agent "Security Audit Specialist"
```

#### B. Documentation Agent (`src/agents/docs_agent.py`)
- **Job**: Generates technical documentation
- **Scope**: READMEs, API docs, architecture diagrams (Mermaid)
- **Output**: Markdown with code examples and diagrams
- **Capabilities**: `documentation generation`, `api documentation`, `architecture documentation`

```bash
omni execute "Generate comprehensive README for this project"
```

#### C. Code Generator Agent (`src/agents/codegen_agent.py`)
- **Job**: Generates and refactors code
- **Standards**: PEP 8, type hints, docstrings
- **Output**: Production-ready code with explanations
- **Capabilities**: `code generation`, `refactoring`, `feature implementation`, `bug fixing`

```bash
omni execute "Create a utility function for batch file processing"
```

### 3. **Agent Orchestrator** (`src/core/orchestrator.py`)

Central routing and management engine for all agents.

```python
class AgentOrchestrator:
    - agents: List[SpecialistAgent]        # Registered agents
    - route_goal()                          # Intelligent routing
    - find_best_agent()                     # Capability matching
    - list_agents()                         # Agent discovery
    - get_execution_history()               # Execution tracking
```

**Routing Algorithm:**
1. For each agent, call `can_handle(goal)` → returns (bool, confidence)
2. Filter agents that return True
3. Select agent with highest confidence score
4. Execute and return results

### 4. **Single-Shot Batching (Preserved)**

The file reading utilities maintain the original single-shot batching logic:

```python
read_codebase_for_audit_single_batch()    # Read all files in one pass
read_context()                            # Flexible context aggregation
read_codebase_for_docs()                  # Doc-specific batching
```

**Why This Matters:**
- Single API call to LLM (efficient token usage)
- Maintains entire codebase context in one request
- Scales to large projects within context window limits

## CLI Commands

### Orchestrator Discovery
```bash
omni agents                          # List all agents
omni agents --name "Security Audit Specialist"  # Agent details
```

### Goal Execution (New Unified Interface)
```bash
omni execute "Your goal here" \
    --context ./src \
    --agent "Specific Agent" \
    --output results.json
```

### Legacy Commands (Still Available)
```bash
omni audit ./src                     # Security audit (uses orchestrator internally)
omni doc ./src                       # Documentation generation
omni ask "prompt" --file src/        # Ad-hoc queries
omni chat --file src/                # Interactive session
omni commit                          # Auto-commit message
```

## Execution Flow

```
User Input (CLI)
    ↓
[CLI Command: audit/ask/execute/doc]
    ↓
[Read context via single-shot batching]
    ↓
[Route through AgentOrchestrator]
    ↓
[Orchestrator.find_best_agent(goal)]
    ↓
[SpecialistAgent.can_handle() scoring]
    ↓
[Select best-matching agent]
    ↓
[Agent.execute(goal, context)]
    ↓
[Generate response via Gemini API]
    ↓
[Format & display results]
    ↓
[Optional: Save to file]
```

## Adding New Specialist Agents

### Step 1: Create Agent Class

```python
# src/agents/my_agent.py
from src.agents.base_agent import SpecialistAgent, AgentConfig

class MySpecialistAgent(SpecialistAgent):
    def __init__(self):
        config = AgentConfig(
            name="My Specialist",
            job_description="...",
            system_prompt="...",
            capabilities=["capability1", "capability2", ...]
        )
        super().__init__(config)
    
    def execute(self, goal: str, context: str, **kwargs):
        # Your implementation
        return {
            "status": "success",
            "agent": self.name,
            "result": ...
        }
    
    def can_handle(self, goal: str) -> tuple[bool, float]:
        # Your routing logic
        return (can_handle, confidence)
```

### Step 2: Register with Orchestrator

```python
# src/core/orchestrator.py
from src.agents.my_agent import MySpecialistAgent

def __init__(self):
    self.agents = [
        SecurityAuditAgent(),
        DocumentationAgent(),
        CodeGeneratorAgent(),
        MySpecialistAgent(),  # Add here
    ]
```

## System Prompt Patterns

Each agent's system prompt should:

1. **Define Role**: "You are a [Title] specialized in [Domain]"
2. **Set Output Format**: Specify JSON, Markdown, code blocks, etc.
3. **Provide Constraints**: Quality standards, style guidelines
4. **Include Examples**: For complex outputs

**Example (Security Agent):**
```
You are an Elite DevSecOps Engineer...
CRITICAL RULE: Return output EXCLUSIVELY in valid JSON format...
Do not include markdown formatting...
```

## Configuration & Extensibility

### Agent Configuration
```python
@dataclass
class AgentConfig:
    name: str                      # Display name
    job_description: str           # What it does
    system_prompt: str             # LLM behavior
    capabilities: list[str]        # Searchable keywords
```

### API Consistency
All agents use:
- Same Gemini 2.5-flash model
- Same configuration (from `config.py`)
- Same execution interface
- Standardized error handling

## Error Handling

**Agent-Level:**
- Try-catch in `execute()` method
- Returns dict with `status: "error"` and error message

**Orchestrator-Level:**
- Validates goal routing
- Returns helpful error messages
- Lists available agents if no match

**CLI-Level:**
- Catches exceptions
- Displays formatted error messages
- Suggests alternatives

## Performance Considerations

1. **Single-Shot Batching**: All files read in one pass → minimal I/O
2. **Smart Routing**: No unnecessary agent initialization
3. **Context Reuse**: Same batched context passed to all agents
4. **Token Efficiency**: One API call per execution

## Next Steps for Enhancement

1. **Add More Agents**: Performance optimizer, refactoring specialist, documentation reviewer
2. **Persistent Memory**: Store execution history, learned patterns
3. **Agent Training**: Fine-tune routing based on feedback
4. **Parallel Execution**: Support for multi-agent sequential workflows
5. **Webhook Support**: External trigger integration

## Testing the Orchestrator

```bash
# Test agent discovery
omni agents

# Test routing to specific agent
omni execute "audit for security issues" --agent "Security Audit Specialist"

# Test automatic routing
omni execute "generate API documentation"

# Test execution history
omni agents  # Shows last 10 executions
```

## Architecture Diagram

```
                    ┌─────────────────────────┐
                    │   CLI Interface (Typer) │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │  File Reader (Batching) │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼──────────────────┐
                    │  AgentOrchestrator             │
                    │ ┌────────────────────────────┐ │
                    │ │ find_best_agent(goal)      │ │
                    │ │ route_goal()               │ │
                    │ └────────────┬────────────────┤ │
                    └─────────────┼──────────────────┘
                                  │
                ┌─────────────────┼─────────────────┐
                │                 │                 │
    ┌───────────▼────────┐ ┌─────▼──────────┐ ┌───▼──────────┐
    │ SecurityAuditAgent │ │ DocsAgent      │ │CodeGenAgent  │
    │ (SAST)             │ │(Markdown)      │ │(Clean Code)  │
    │                    │ │                │ │              │
    │ system_prompt:...  │ │system_prompt:..│ │system_prompt:│
    │ can_handle()       │ │can_handle()    │ │can_handle()  │
    │ execute()          │ │execute()       │ │execute()     │
    └─────────┬──────────┘ └────────┬───────┘ └───┬──────────┘
              │                     │              │
              │                     │              │
              └─────────────────────┼──────────────┘
                                    │
                        ┌───────────▼────────────┐
                        │  Gemini 2.5-Flash API  │
                        │  (Single-shot request) │
                        └────────────────────────┘
```

## Tech Stack

- **Language**: Python 3.11+
- **AI**: Google Gemini 2.5-Flash API
- **CLI**: Typer (with Rich for formatting)
- **Architecture**: Clean Architecture with Dependency Injection
- **Type Safety**: Full type hints on all modules

# Migration Guide: Single Agent → Multi-Agent Orchestrator

## Overview

Your Omni Agent has been successfully refactored from a single-purpose CLI auditor into a **flexible multi-agent orchestrator platform**. This guide explains what changed and how to migrate your workflows.

## What Changed?

### Before: Single-Agent Architecture
```
User Input (Goal)
    ↓
[OmniEngine] (single LLM client)
    ↓
[SAST Analysis Only]
    ↓
[Output: JSON or Markdown]
```

### After: Multi-Agent Orchestrator
```
User Input (Goal)
    ↓
[AgentOrchestrator] (intelligent router)
    ↓
[Smart Agent Selection] (based on goal analysis)
    ↓
[Choose: Security | Documentation | CodeGen | ? ]
    ↓
[Agent.execute(goal, context)]
    ↓
[Output: Formatted results]
```

## Key Improvements

| Aspect | Before | After |
|--------|--------|-------|
| **Capabilities** | Security audits only | Security, Docs, Code Gen, Extensible |
| **Goal Routing** | Manual selection | Automatic intelligent routing |
| **Extensibility** | Hard to add agents | Easy to create new agents |
| **CLI Experience** | Domain-specific commands | Unified `execute` command |
| **Agent Config** | Hardcoded prompts | Configurable per-agent |
| **Capability Discovery** | None | `omni agents` command |

## Migration Paths

### Migration Path 1: Keep Using Legacy Commands (No Changes)

All old commands still work! They now use the orchestrator internally:

```bash
# These still work EXACTLY as before
omni audit ./src
omni doc ./src
omni ask "your question" --file ./src
omni chat --file ./src
omni commit
```

**Status**: ✅ **Fully backward compatible**

### Migration Path 2: Use New Unified `execute` Command (Recommended)

Replace legacy commands with the new unified interface:

**Old way:**
```bash
omni audit ./src
```

**New way:**
```bash
omni execute "Perform security audit" --context ./src
# Orchestrator auto-routes to Security Audit Agent
```

**Benefits:**
- Consistent interface for all tasks
- Automatic routing (no need to remember which command to use)
- Flexible output options (JSON, console, file)
- Extensible (works with all future agents)

### Migration Path 3: Explicit Agent Selection

When you know exactly which agent you need:

```bash
# Force specific agent
omni execute "goal" \
    --agent "Security Audit Specialist" \
    --context ./src
```

## New Features to Explore

### 1. Agent Discovery

```bash
# List all available agents
omni agents

# Get details on specific agent
omni agents --name "Security Audit Specialist"
```

### 2. Flexible Output

```bash
# Save structured results
omni execute "goal" --output results.json

# View in console (default)
omni execute "goal"
```

### 3. Intelligent Routing

The orchestrator automatically selects the best agent:

```bash
# Routes to Security Agent
omni execute "Find vulnerabilities"

# Routes to Documentation Agent
omni execute "Generate README"

# Routes to Code Gen Agent
omni execute "Create utility function"

# You decide which agent to use
omni execute "goal" --agent "Code Generator Specialist"
```

## Use Case Migrations

### Use Case 1: Security Audit Workflow

**Old workflow:**
```bash
omni audit ./src
# Output: OMNI_AUDIT.json, OMNI_SECURITY_REPORT.md
```

**New workflow (option 1 - backward compatible):**
```bash
omni audit ./src
# Same output, now uses orchestrator internally
```

**New workflow (option 2 - using execute):**
```bash
omni execute "Comprehensive SAST analysis" \
    --context ./src \
    --output security_audit.json
```

### Use Case 2: Ad-hoc Queries

**Old workflow:**
```bash
omni ask "How does authentication work?" --file ./src
omni ask "Explain this function" --file ./src/utility.py
```

**New workflow:**
```bash
# Routes to Code Generator or Documentation Agent
omni execute "Explain the authentication system" --context ./src

# More control over agent selection
omni execute "Explain this function" \
    --context ./src/utility.py \
    --agent "Code Generator Specialist"
```

### Use Case 3: Documentation Generation

**Old workflow:**
```bash
omni doc ./src
# Output: OMNI_DOCS.md
```

**New workflow (backward compatible):**
```bash
omni doc ./src
# Works exactly as before
```

**New workflow (using execute):**
```bash
omni execute "Generate comprehensive project documentation" \
    --context . \
    --output docs.json
```

## Command Reference: Old → New

| Old Command | Equivalent New Command | Status |
|-------------|------------------------|--------|
| `omni audit ./src` | `omni execute "audit" --context ./src` | ✅ Both work |
| `omni doc ./src` | `omni execute "document" --context ./src` | ✅ Both work |
| `omni ask "q" --file ./src` | `omni execute "q" --context ./src` | ✅ Both work |
| `omni chat --file ./src` | `omni chat --file ./src` | ✅ Still works |
| `omni commit` | `omni commit` | ✅ Still works |

**New exclusive commands:**
| Command | Purpose |
|---------|---------|
| `omni agents` | List all agents |
| `omni execute` | Unified goal execution |

## Architecture Changes

### New Directory Structure

```
src/
├── agents/              # NEW: Specialist agents module
│   ├── __init__.py
│   ├── base_agent.py         # Base class for all agents
│   ├── security_agent.py      # SAST specialist
│   ├── docs_agent.py          # Documentation specialist
│   └── codegen_agent.py       # Code generation specialist
├── core/
│   ├── config.py
│   ├── llm_client.py          # Unchanged
│   └── orchestrator.py        # NEW: Agent routing system
├── cli/
│   └── main.py               # UPDATED: Orchestrator integration
└── utils/
    └── file_reader.py        # Unchanged (single-shot batching preserved)
```

### New Classes

```python
# src/agents/base_agent.py
SpecialistAgent        # Abstract base class
AgentConfig           # Configuration dataclass

# src/agents/security_agent.py
SecurityAuditAgent    # SAST specialist

# src/agents/docs_agent.py
DocumentationAgent    # Documentation specialist

# src/agents/codegen_agent.py
CodeGeneratorAgent    # Code generation specialist

# src/core/orchestrator.py
AgentOrchestrator     # Central routing engine
```

### Preserved Components

✅ **Nothing was removed or broken!**

- `OmniEngine` class (still works for custom queries)
- `read_context()` functions (batching logic unchanged)
- All file reading utilities
- Configuration system
- Gemini API integration

## Debugging Guide

### "No suitable agent found" Error

**Cause**: Goal was too vague for routing algorithm

**Solution**: Be more specific with keywords
```bash
# ❌ Too vague
omni execute "analyze this"

# ✅ Clear goal
omni execute "audit for security vulnerabilities"
```

### Agent doesn't seem right for my goal

**Solution**: Force specific agent
```bash
omni execute "goal" --agent "Agent Name"

# List agents to find exact name
omni agents
```

### Context too large

**Solution**: Use smaller context
```bash
# Instead of:
omni execute "goal" --context ./

# Use:
omni execute "goal" --context ./src/specific_module
```

## Performance Considerations

✅ **Performance improved:**
- Single-shot batching preserved (no I/O overhead)
- Intelligent agent selection (no unnecessary initialization)
- Smart routing (automatic and fast)

The orchestrator adds negligible overhead compared to the improvement in flexibility.

## Next Steps

### For Current Users
1. Keep using your existing commands - they work!
2. Gradually explore new `execute` command
3. Try `omni agents` to discover capabilities
4. Check USER_GUIDE_ORCHESTRATOR.md for advanced usage

### For Extension
1. See ORCHESTRATOR_ARCHITECTURE.md for adding new agents
2. Create custom specialist agents for your domain
3. Register them with the orchestrator
4. Extend capabilities without modifying existing code

### For Integration
1. Use `omni execute` with `--output` for CI/CD pipelines
2. Leverage structured JSON output for parsing
3. Script multiple agent executions for workflows
4. See USER_GUIDE_ORCHESTRATOR.md for CI/CD examples

## FAQ

**Q: Will my existing scripts break?**
A: No! All legacy commands work exactly as before.

**Q: Should I migrate to the new `execute` command?**
A: Not required, but recommended for:
- New workflows
- Better consistency
- Future extensibility
- Easier maintenance

**Q: Can I create my own agents?**
A: Yes! See ORCHESTRATOR_ARCHITECTURE.md for detailed guide on creating custom specialist agents.

**Q: Does this support async/parallel agent execution?**
A: Current version: single agent per execution (sequential).
- Planned: parallel multi-agent workflows coming soon!

**Q: Is the system still efficient after refactoring?**
A: Yes! Single-shot batching preserved, minimal overhead, same token efficiency.

**Q: What about the Gemini API costs?**
A: Unchanged! Same API, same costs, more functionality.

## Support

For issues or questions about the migration:
1. Check USER_GUIDE_ORCHESTRATOR.md for usage examples
2. Review ORCHESTRATOR_ARCHITECTURE.md for architecture details
3. Check agent details: `omni agents --name "Agent Name"`
4. Review error messages for helpful hints

---

**Refactoring Summary:**
- ✅ Backward compatible (all old commands work)
- ✅ New unified interface (omni execute)
- ✅ Intelligent routing (automatic agent selection)
- ✅ Extensible architecture (easy to add agents)
- ✅ Preserved performance (single-shot batching)
- ✅ Same tech stack (Python/Gemini)

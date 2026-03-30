# What's New: Omni Agent v2.0 - Multi-Agent Orchestrator

## 🚀 Quick Overview

Your Omni Agent has been refactored into a **multi-agent orchestrator platform** with intelligent routing, specialist agents, and extensible architecture.

### What You Get

✅ **3 Specialist Agents Ready to Use:**
- Security Audit Specialist (SAST analysis)
- Documentation Specialist (auto-generates docs)
- Code Generator Specialist (generates code)

✅ **Intelligent Routing:**
- Automatically selects the best agent for your goal
- No more wondering which command to use

✅ **Unified Interface:**
```bash
omni execute "Your goal here" --context ./src
# Orchestrator auto-routes to appropriate agent
```

✅ **Fully Backward Compatible:**
```bash
# All your old commands still work!
omni audit ./src
omni doc ./src
omni ask "question" --file ./src
```

✅ **Easy to Extend:**
- Add custom specialist agents following included template
- Framework already established
- Guides and examples provided

---

## 🎯 Getting Started (30 seconds)

### 1. Discover Available Agents
```bash
omni agents
```

### 2. Execute a Goal
```bash
# Let orchestrator choose best agent
omni execute "Find security vulnerabilities" --context ./src

# Or force specific agent
omni execute "goal" --agent "Code Generator Specialist" --context ./src
```

### 3. Save Results
```bash
omni execute "goal" --context ./src --output results.json
```

That's it! The orchestrator handles the rest.

---

## 📚 Documentation Structure

| Document | Purpose | Read When |
|----------|---------|-----------|
| **README_ORCHESTRATOR.md** | 📖 Quick reference | Starting out |
| **ORCHESTRATOR_ARCHITECTURE.md** | 🏗️ Technical design | Understanding system |
| **USER_GUIDE_ORCHESTRATOR.md** | 💡 Usage examples | Learning workflows |
| **MIGRATION_GUIDE.md** | 🔄 Upgrade path | Using existing scripts |
| **AGENT_DEVELOPMENT_GUIDE.md** | 🛠️ Build custom agents | Extending system |
| **REFACTORING_SUMMARY.md** | 📋 What changed | Full overview |
| **CHANGELOG.md** | 📝 Changes & stats | Detailed changes |

---

## 🏗️ Architecture at a Glance

```
┌─────────────────────┐
│   User Input (CLI)  │
└──────────┬──────────┘
           │
┌──────────▼──────────────────┐
│   AgentOrchestrator          │
│  (Intelligent Router)        │
└──────────┬───────────────────┘
           │
    ┌──────┴──────┬─────────────┬─────────────┐
    │             │             │             │
┌───▼──┐   ┌──────▼──┐   ┌──────▼──┐    ┌───▼────────┐
│Sec   │   │Docs     │   │CodeGen  │    │   Custom   │
│Audit │   │Agent    │   │Agent    │    │   Agents   │
└───┬──┘   └──┬──────┘   └──┬──────┘    └────┬───────┘
    │         │            │               │
    └─────────┴────────────┴───────────────┘
                  │
        ┌─────────▼────────┐
        │  Gemini API      │
        │ (2.5-Flash)      │
        └──────────────────┘
```

---

## 🆕 New Commands

### `omni agents`
List all available specialist agents:
```bash
omni agents

# Output:
# ┌─────────────────────────────────────────────┐
# │ Available Specialist Agents                 │
# ├─────────────────────────────────────────────┤
# │ Security Audit Specialist                   │
# │ Documentation Specialist                    │
# │ Code Generator Specialist                   │
# └─────────────────────────────────────────────┘
```

Get details on specific agent:
```bash
omni agents --name "Security Audit Specialist"
```

### `omni execute`
Unified goal execution interface:
```bash
# Auto-routing (orchestrator picks best agent)
omni execute "Your goal" --context ./src

# Options:
#   --context PATH      Where to read code from (default: .)
#   --agent NAME        Force specific agent (optional)
#   --output FILE       Save results to JSON
```

---

## ✅ Backward Compatibility

**All old commands still work exactly the same:**

```bash
omni audit ./src       # ✅ Works (uses orchestrator internally)
omni doc ./src         # ✅ Works (unchanged)
omni ask "Q" --file ./ # ✅ Works (unchanged)
omni chat --file ./src # ✅ Works (unchanged)
omni commit            # ✅ Works (unchanged)
```

**No breaking changes. No migration required.**

---

## 🛠️ Usage Examples

### Security Audit
```bash
# Auto-routed to Security Audit Agent
omni execute "Find all security vulnerabilities" --context ./src

# Save audit results
omni execute "Security audit" --context ./src --output audit.json
```

### Generate Documentation
```bash
# Auto-routed to Documentation Agent
omni execute "Generate comprehensive project README" --context .
```

### Generate Code
```bash
# Auto-routed to Code Generator Agent
omni execute "Create a utility function for batch file uploads" --context ./src

# Force agent explicitly
omni execute "goal" --agent "Code Generator Specialist" --context ./src
```

---

## 🔌 Extending the System

### Create Custom Agent (5 minutes)

1. Create `src/agents/my_agent.py`:
```python
from src.agents.base_agent import SpecialistAgent, AgentConfig

class MyAgent(SpecialistAgent):
    def __init__(self):
        config = AgentConfig(
            name="My Specialist",
            job_description="What this agent does",
            system_prompt="LLM behavior instructions",
            capabilities=["keyword1", "keyword2"]
        )
        super().__init__(config)
    
    def execute(self, goal, context, **kwargs):
        # Your implementation here
        return {"status": "success", "result": "..."}
    
    def can_handle(self, goal):
        # Your routing logic
        return (True, 0.9)  # (can_handle, confidence)
```

2. Register in `src/core/orchestrator.py`:
```python
from src.agents.my_agent import MyAgent

def __init__(self):
    self.agents = [
        ...,
        MyAgent(),  # Add your agent
    ]
```

3. Test:
```bash
omni agents | grep "My Specialist"
omni execute "goal with your keywords"
```

Full guide in `AGENT_DEVELOPMENT_GUIDE.md`

---

## 🔍 Troubleshooting

### "No suitable agent found"
- Goal was too vague
- **Fix**: Be specific with keywords
  ```bash
  omni execute "Perform security audit"  # ✅ Better
  ```

### Agent doesn't seem right
- **Fix**: Force the agent
  ```bash
  omni execute "goal" --agent "Agent Name"
  ```

### Context too large
- **Fix**: Use smaller context
  ```bash
  omni execute "goal" --context ./src/module  # Not: ./
  ```

### API Error
- **Fix**: Check `.env` has `GEMINI_API_KEY`
  ```bash
  echo $GEMINI_API_KEY  # Should not be empty
  ```

---

## 📊 Key Statistics

| Metric | Value |
|--------|-------|
| Specialist Agents | 3 (+ extensible) |
| New CLI Commands | 2 (`agents`, `execute`) |
| Backward Compatibility | 100% |
| Breaking Changes | 0 |
| New Documentation Pages | 5 guides |
| Lines of New Code | ~610 |
| Lines of Documentation | ~1,500+ |

---

## 🎓 Learning Path

### I Want to...

**Use the new system:**
1. Run `omni agents` to see agents
2. Try `omni execute "goal"`
3. Save results with `--output file.json`

**Understand the architecture:**
1. Read `ORCHESTRATOR_ARCHITECTURE.md`
2. Review `USER_GUIDE_ORCHESTRATOR.md`
3. Check example workflows

**Create custom agents:**
1. Read `AGENT_DEVELOPMENT_GUIDE.md`
2. Follow the template
3. Register in orchestrator
4. Test with `omni agents`

**Migrate existing scripts:**
1. Read `MIGRATION_GUIDE.md`
2. All old commands work as-is
3. Gradually adopt `omni execute`

**Get full refactoring details:**
1. Read `REFACTORING_SUMMARY.md`
2. Check `CHANGELOG.md`
3. Review code changes

---

## 🚀 What's Next?

### Immediate (Try It Now)
```bash
omni agents                          # See available agents
omni execute "Find vulnerabilities" # Test auto-routing
```

### Short Term (Next Use)
- Try different goals to see routing
- Save results with `--output`
- Use in existing workflows

### Medium Term (Next Project)
- Create your first custom agent
- Build workflows using agent outputs
- Share custom agents with team

### Long Term
- Maintain custom agent library
- Explore parallel agent execution
- Contribute improvements

---

## 📞 Need Help?

**Quick Answers:**
- `omni agents` - See available agents
- `omni agents --name "Agent"` - Agent details
- Check documentation files above

**Common Tasks:**
- Usage examples → `USER_GUIDE_ORCHESTRATOR.md`
- Create agents → `AGENT_DEVELOPMENT_GUIDE.md`
- Upgrade scripts → `MIGRATION_GUIDE.md`
- Technical details → `ORCHESTRATOR_ARCHITECTURE.md`

**Troubleshooting:**
1. Read documentation for your task
2. Check error message carefully
3. Try forcing specific agent: `--agent "Name"`
4. Check context size is reasonable
5. Verify API key is set

---

## ✨ Why This Matters

### Before: Single-Purpose Tool
- Only security audits
- Limited to one use case
- Hard to extend

### After: Flexible AI Platform
- ✅ Multiple specialists
- ✅ Intelligent routing
- ✅ Easy to extend
- ✅ Growing capabilities
- ✅ Same performance
- ✅ Perfect compatibility

---

## 📦 What's Included

```
New Files:
├── src/agents/
│   ├── base_agent.py          (foundation)
│   ├── security_agent.py       (specialist)
│   ├── docs_agent.py           (specialist)
│   ├── codegen_agent.py        (specialist)
│   └── __init__.py             (exports)
├── src/core/orchestrator.py    (routing)
└── Documentation/
    ├── ORCHESTRATOR_ARCHITECTURE.md
    ├── USER_GUIDE_ORCHESTRATOR.md
    ├── MIGRATION_GUIDE.md
    ├── AGENT_DEVELOPMENT_GUIDE.md
    ├── REFACTORING_SUMMARY.md
    └── CHANGELOG.md
```

---

## 🎯 TL;DR

**Old Way:**
```bash
omni audit ./src  # Only security
```

**New Way:**
```bash
omni agents                               # See all specialists
omni execute "your goal" --context ./src # Smart routing
```

**Result:**
- More capable
- Better organized  
- Fully extensible
- Completely backward compatible

---

**Get Started:** `omni agents`  
**Questions?** Check the documentation files above.  
**Ready to extend?** See `AGENT_DEVELOPMENT_GUIDE.md`

**Status:** ✅ Production Ready | **Version:** 2.0.0


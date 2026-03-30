# Omni Agent Orchestrator - User Guide

## Quick Start

### 1. Check Available Agents

```bash
omni agents
```

Output:
```
  Available Specialist Agents

Agent Name                    Job Description                  Capabilities
─────────────────────────────────────────────────────────────────────────────
Security Audit Specialist     Performs automated SAST...       security audit, vulnerability detection, sast, ...
Documentation Specialist      Generates comprehensive...       documentation generation, readme writing, ...
Code Generator Specialist     Generates new code features...   code generation, refactoring, feature...
```

### 2. Get Details on Specific Agent

```bash
omni agents --name "Security Audit Specialist"
```

### 3. Execute a Goal (Auto-Routing)

The orchestrator automatically selects the best agent based on your goal:

```bash
# Automatically routes to Security Audit Agent
omni execute "Find security vulnerabilities in this codebase" --context ./src

# Automatically routes to Documentation Agent
omni execute "Generate comprehensive API documentation"

# Automatically routes to Code Generator Agent
omni execute "Create a utility function for handling file uploads"
```

### 4. Force Specific Agent

If you want to use a specific agent:

```bash
omni execute "audit for OWASP compliance" \
    --agent "Security Audit Specialist" \
    --context ./src \
    --output security_report.json
```

### 5. Save Results

```bash
omni execute "Generate project documentation" \
    --output docs_output.json
```

## Use Case Examples

### Security Audit Workflow

```bash
# Run comprehensive security audit
omni execute "Perform SAST analysis and identify all vulnerabilities" \
    --context ./src

# Audit specific module
omni execute "Audit security of authentication module" \
    --context ./src/auth \
    --agent "Security Audit Specialist" \
    --output auth_security_report.json
```

**Output Example:**
```json
{
  "status": "success",
  "agent": "Security Audit Specialist",
  "result": {
    "audit_summary": {
      "total_vulnerabilities": 3,
      "critical_count": 1,
      "high_count": 1,
      "medium_count": 1,
      "low_count": 0
    },
    "findings": [
      {
        "severity": "CRITICAL",
        "vulnerability_type": "SQL Injection",
        "file_path": "src/db/queries.py",
        "line_number_or_function": "execute_query()",
        "description": "User input directly concatenated into SQL query",
        "remediation_code": "Use parameterized queries with prepared statements"
      }
    ]
  }
}
```

### Code Generation Workflow

```bash
# Generate new feature code
omni execute "Create a REST API endpoint for user management" \
    --context ./src \
    --agent "Code Generator Specialist"

# Refactor existing code
omni execute "Refactor the payment processing module to use a factory pattern" \
    --context ./src/payment \
    --output refactored_code.json

# Fix bugs
omni execute "Analyze code and suggest fixes for performance issues" \
    --context ./src/performance_critical
```

### Documentation Workflow

```bash
# Generate README
omni execute "Generate a professional README with setup instructions" \
    --context .

# API documentation
omni execute "Create detailed API documentation with examples" \
    --context ./src/api

# Architecture documentation
omni execute "Document the system architecture with Mermaid diagrams" \
    --context ./src
```

## Legacy Commands (Still Supported)

### Security Audit

```bash
# Old way (still works, now uses orchestrator internally)
omni audit ./src
```

This command:
1. Reads context using single-shot batching
2. Routes to Security Audit Agent via orchestrator
3. Saves to `OMNI_AUDIT.json` and `OMNI_SECURITY_REPORT.md`

### Generate Documentation

```bash
omni doc ./src
```

### Interactive Chat

```bash
omni chat --file ./src
```

### Auto-Commit Message

```bash
omni commit
```

### Ad-hoc Query

```bash
omni ask "How does the authentication work?" --file ./src
```

## Advanced Usage

### Batch Security Audits

```bash
# Audit multiple folders
for dir in src/modules/*; do
    echo "Auditing $dir..."
    omni execute "Audit for security vulnerabilities" \
        --context "$dir" \
        --output "${dir}_audit.json" \
        --agent "Security Audit Specialist"
done
```

### Generate Full Documentation Suite

```bash
# Create comprehensive documentation
omni execute "Generate README with installation, usage, and contribution guidelines" \
    --context . \
    --output README_generated.md

omni execute "Create API documentation with all endpoints and examples" \
    --context ./src/api \
    --output API_DOCS_generated.md

omni execute "Generate architecture diagram in Mermaid format" \
    --context ./src \
    --output ARCHITECTURE_generated.md
```

### Code Refactoring Pipeline

```bash
# First: Identify issues
omni execute "Analyze code quality and identify refactoring opportunities" \
    --context ./src \
    --output code_analysis.json

# Second: Generate refactored code
omni execute "Refactor to improve code quality and maintainability" \
    --context ./src \
    --output refactored_code_suggestions.json

# Third: Security check
omni execute "Verify no security issues introduced in refactoring" \
    --context ./src \
    --output final_security_check.json
```

## Output Formats

### JSON Output (All Agents)
```bash
omni execute "goal" --output results.json
# Saves structured result with status, agent name, and result payload
```

### Markdown Output (Documentation)
```bash
# Documentation agent returns Markdown with code blocks and Mermaid diagrams
omni execute "Generate documentation" | tee docs.md
```

### Console Output (Rich Formatting)
```bash
# Default: Beautiful console output with colors and tables
omni execute "Audit codebase"
# [✅ Executed by: Security Audit Specialist]
# ┌─────────────────────────────────────┐
# │ Risk Level      │ CRITICAL RISK ⚠ │
# │ Total Vulns     │ 5               │
# │ Critical        │ 2               │
# └─────────────────────────────────────┘
```

## Troubleshooting

### "No suitable agent found for this goal"

**Solution:** Be more specific with goal keywords:
```bash
# ❌ Too vague
omni execute "Check this"

# ✅ Clear goal
omni execute "Perform a security audit to find vulnerabilities"
```

### Agent doesn't seem right for my goal

**Solution:** Force specific agent:
```bash
omni execute "goal" --agent "Agent Name"

# List all agents to find exact name
omni agents
```

### Context too large

**Solution:** Use smaller context:
```bash
# Too large
omni execute "goal" --context ./

# Better
omni execute "goal" --context ./src/specific_module
```

### API Token Limits

**Solution:** 
- Audit smaller directories
- Use more specific goals to reduce output size
- Check context size: `du -sh ./src`

## Tips & Best Practices

1. **Be Specific**: Detailed goals → better routing and results
   ```bash
   omni execute "Find SQL injection vulnerabilities in database layer" 
   # Better than: "Check for issues"
   ```

2. **Use Appropriate Context**: Only include relevant code
   ```bash
   omni execute "audit --context ./src/auth"  # Not: --context ./
   ```

3. **Chain Commands**: Use output of one agent for another
   ```bash
   omni execute "Identify code issues" --output analysis.json
   omni execute "Fix identified issues" --context ./src
   ```

4. **Check Agent Details**: Know what each agent does
   ```bash
   omni agents --name "Security Audit Specialist"
   ```

5. **Save Results**: Always backup important outputs
   ```bash
   omni execute "goal" --output backup_$(date +%s).json
   ```

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Omni Security Audit
on: [push]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Run security audit
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
        run: omni execute "Comprehensive security audit" --context ./src --output audit.json
      
      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: security-audit
          path: audit.json
```

## Performance Tips

1. **Single-Shot Batching**: All files read at once → faster than sequential reads
2. **Smart Agent Selection**: Automatic routing → no manual selection overhead
3. **Token Efficiency**: One API call per execution → minimal latency
4. **Caching Context**: Reuse context for multiple operations:
   ```bash
   CONTEXT=$(omni read-context ./src)
   omni execute "goal1" 
   omni execute "goal2" 
   # (runs faster as context already read)
   ```

## Next Steps

- Explore agent capabilities: `omni agents`
- Create custom agents (see ORCHESTRATOR_ARCHITECTURE.md for extending)
- Integrate with your CI/CD pipeline
- Set up automation workflows

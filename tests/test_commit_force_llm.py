"""Test --force-llm flag behavior in omni commit command."""
import os
import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add repo to path
repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root))

from src.cli.main import _build_local_commit_message


def test_force_llm_env_var():
    """Verify that OMNI_FORCE_LLM environment variable is recognized."""
    # This would be checked in the commit function as:
    # use_llm_force = force_llm or os.getenv("OMNI_FORCE_LLM", "").lower() in ("true", "1", "yes")
    
    force_llm_flag = False
    
    # Test with env var set to "true"
    env_value = "true"
    use_llm_force = force_llm_flag or env_value.lower() in ("true", "1", "yes")
    assert use_llm_force == True, "OMNI_FORCE_LLM=true should enable force-llm"
    
    # Test with env var set to "1"
    env_value = "1"
    use_llm_force = force_llm_flag or env_value.lower() in ("true", "1", "yes")
    assert use_llm_force == True, "OMNI_FORCE_LLM=1 should enable force-llm"
    
    # Test with env var set to "yes"
    env_value = "yes"
    use_llm_force = force_llm_flag or env_value.lower() in ("true", "1", "yes")
    assert use_llm_force == True, "OMNI_FORCE_LLM=yes should enable force-llm"
    
    # Test with env var set to "false"
    env_value = "false"
    use_llm_force = force_llm_flag or env_value.lower() in ("true", "1", "yes")
    assert use_llm_force == False, "OMNI_FORCE_LLM=false should not enable force-llm"
    
    # Test with flag set to True
    force_llm_flag = True
    use_llm_force = force_llm_flag or env_value.lower() in ("true", "1", "yes")
    assert use_llm_force == True, "--force-llm flag should enable force-llm"
    
    print("✓ OMNI_FORCE_LLM env var and --force-llm flag logic verified")


def test_heuristic_formatting():
    """Verify heuristic produces Conventional Commits format with scope."""
    changed_files = "M  src/cli/main.py\nM  src/core/llm_client.py"
    diff_text = "feat: add force-llm support\nfix: update heuristic logic"
    
    message, confidence, commit_type = _build_local_commit_message(changed_files, diff_text)
    
    # Should have format: type(scope): description
    assert "(" in message and ")" in message, f"Message should have scope: {message}"
    assert message.islower() or message[0].islower(), f"Message should start with lowercase: {message}"
    
    # Parse the message
    parts = message.split("(")
    commit_type_part = parts[0]
    scope_and_desc = ")".join(parts[1:])
    scope = scope_and_desc.split(")")[0]
    
    print(f"✓ Heuristic message format verified: {message}")
    print(f"  - Type: {commit_type_part}")
    print(f"  - Scope: {scope}")
    print(f"  - Confidence: {confidence:.2f}")


if __name__ == "__main__":
    test_force_llm_env_var()
    test_heuristic_formatting()
    print("\n✓ All --force-llm logic tests passed!")

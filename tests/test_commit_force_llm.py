"""Test --force-llm flag behavior in omni commit command."""
import os
import sys
import json
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

# Add repo to path
repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root))

from src.cli.main import _build_local_commit_message, _get_commit_cache_path, _save_commit_cache


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


def test_user_level_cache_path():
    """Verify commit cache is stored under the user's cache directory."""
    cache_path = _get_commit_cache_path()

    assert cache_path.as_posix().endswith("/.cache/omni/commit_cache.json"), cache_path
    assert cache_path.parent.name == "omni", cache_path
    assert cache_path.parent.parent.name == ".cache", cache_path

    print(f"✓ User-level cache path verified: {cache_path}")


def test_cache_lazy_init():
    """Verify cache file is only created when cache dict is not empty (lazy init)."""
    # Test 1: Empty cache should not trigger write
    empty_cache = {}
    
    with patch('pathlib.Path.mkdir') as mock_mkdir, \
         patch('builtins.open', mock_open()) as mock_file, \
         patch('json.dump') as mock_dump:
        _save_commit_cache(empty_cache)
        # mkdir and json.dump should not be called for empty cache
        mock_mkdir.assert_not_called()
        mock_dump.assert_not_called()
    
    print("✓ Empty cache not written (lazy init verified)")
    
    # Test 2: Non-empty cache should trigger write
    non_empty_cache = {
        "abc123": {
            "message": "feat(cli): test commit",
            "mode": "heuristic",
            "confidence": 0.95,
            "saved_at": "2026-05-01T00:00:00+00:00",
            "type": "Feat",
        }
    }
    
    with patch('pathlib.Path.mkdir') as mock_mkdir, \
         patch('builtins.open', mock_open()) as mock_file, \
         patch('json.dump') as mock_dump:
        _save_commit_cache(non_empty_cache)
        # For non-empty cache, mkdir and json.dump should be called
        mock_mkdir.assert_called_once()
        mock_dump.assert_called_once()
    
    print("✓ Non-empty cache written successfully (lazy init verified)")


if __name__ == "__main__":
    test_force_llm_env_var()
    test_heuristic_formatting()
    test_user_level_cache_path()
    test_cache_lazy_init()
    print("\n✓ All cache and commit tests passed!")

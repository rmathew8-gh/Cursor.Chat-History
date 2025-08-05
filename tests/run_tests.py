#!/usr/bin/env python3
"""
Simple test runner for the Cursor Chat History Exporter.
Run with: python3 run_tests.py
"""

import sys
import os
from pathlib import Path

# Add the current directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from tests.test_cursor_chat_history import *

def run_all_tests():
    """Run all test functions and report results."""
    test_functions = [
        test_extract_ai_service_prompts,
        test_prompt_dataclass_with_timestamp,
        test_prompt_dataclass_without_timestamp,
        test_parse_prompts_with_timestamp,
        test_parse_prompts_without_timestamp,
        test_export_prompts_to_org_with_timestamps,
        test_export_prompts_to_org_without_timestamps,
        test_export_prompts_to_org_mixed_timestamps,
        test_timestamp_formatting,
        test_error_handling_missing_timestamp,
        test_backward_compatibility
    ]
    
    print("🧪 Running Cursor Chat History Exporter Tests")
    print("=" * 50)
    
    passed = 0
    failed = 0
    
    for test_func in test_functions:
        try:
            test_func()
            print(f"✓ {test_func.__name__}")
            passed += 1
        except Exception as e:
            print(f"✗ {test_func.__name__}: {e}")
            failed += 1
    
    print("=" * 50)
    print(f"Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed!")
        return True
    else:
        print("❌ Some tests failed!")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1) 
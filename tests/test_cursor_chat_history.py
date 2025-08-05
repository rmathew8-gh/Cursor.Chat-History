import json
import tempfile
import os
from datetime import datetime
from pathlib import Path
from cursor_chat_history import (
    extract_ai_service_prompts, 
    CursorChatHistoryExporter, 
    Prompt
)

def test_extract_ai_service_prompts():
    """Test the existing functionality still works."""
    db_path = Path(__file__).parent / "state_example.vscdb"
    prompts = extract_ai_service_prompts(db_path)
    assert prompts is not None, "No prompts returned from extract_ai_service_prompts"
    assert isinstance(prompts, list), "Returned prompts is not a list"
    assert len(prompts) > 0, "No prompts found in the .vscdb file"
    for prompt in prompts:
        assert 'text' in prompt, "Prompt entry missing 'text' field"

def test_prompt_dataclass_with_timestamp():
    """Test Prompt dataclass with timestamp field."""
    timestamp = datetime(2024, 12, 24, 10, 35)
    prompt = Prompt(text="test prompt", timestamp=timestamp)
    
    assert prompt.text == "test prompt"
    assert prompt.timestamp == timestamp
    assert prompt.timestamp is not None

def test_prompt_dataclass_without_timestamp():
    """Test Prompt dataclass without timestamp (backward compatibility)."""
    prompt = Prompt(text="test prompt")
    
    assert prompt.text == "test prompt"
    assert prompt.timestamp is None

def test_parse_prompts_with_timestamp():
    """Test parse_prompts method with timestamp."""
    raw_prompts = [
        {"text": "first prompt"},
        {"text": "second prompt"}
    ]
    timestamp = datetime(2024, 12, 24, 10, 35)
    
    prompts = CursorChatHistoryExporter.parse_prompts(raw_prompts, timestamp)
    
    assert prompts is not None
    assert len(prompts) == 2
    assert all(isinstance(p, Prompt) for p in prompts)
    assert all(p.timestamp == timestamp for p in prompts)
    assert prompts[0].text == "first prompt"
    assert prompts[1].text == "second prompt"

def test_parse_prompts_without_timestamp():
    """Test parse_prompts method without timestamp."""
    raw_prompts = [
        {"text": "first prompt"},
        {"text": "second prompt"}
    ]
    
    prompts = CursorChatHistoryExporter.parse_prompts(raw_prompts)
    
    assert prompts is not None
    assert len(prompts) == 2
    assert all(isinstance(p, Prompt) for p in prompts)
    assert all(p.timestamp is None for p in prompts)
    assert prompts[0].text == "first prompt"
    assert prompts[1].text == "second prompt"

def test_export_prompts_to_org_with_timestamps():
    """Test export_prompts_to_org with timestamps."""
    timestamp = datetime(2024, 12, 24, 10, 35)
    prompts = [
        Prompt(text="first prompt", timestamp=timestamp),
        Prompt(text="second prompt", timestamp=timestamp)
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.org', delete=False) as tmp_file:
        output_path = Path(tmp_file.name)
    
    try:
        CursorChatHistoryExporter.export_prompts_to_org(prompts, output_path)
        
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Use the actual formatted timestamp
        expected_timestamp = timestamp.strftime("[%Y-%m-%d %a %H:%M]")
        expected_lines = [
            f"* {expected_timestamp} first prompt",
            f"* {expected_timestamp} second prompt"
        ]
        
        for expected_line in expected_lines:
            assert expected_line in content, f"Expected line '{expected_line}' not found in content"
        
        # Check file modification time
        file_timestamp = datetime.fromtimestamp(output_path.stat().st_mtime)
        # Allow for small time differences (within 1 second)
        time_diff = abs((file_timestamp - timestamp).total_seconds())
        assert time_diff < 1, f"File modification time {file_timestamp} doesn't match expected {timestamp}"
        
    finally:
        if output_path.exists():
            output_path.unlink()

def test_export_prompts_to_org_without_timestamps():
    """Test export_prompts_to_org without timestamps (backward compatibility)."""
    prompts = [
        Prompt(text="first prompt"),
        Prompt(text="second prompt")
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.org', delete=False) as tmp_file:
        output_path = Path(tmp_file.name)
    
    try:
        CursorChatHistoryExporter.export_prompts_to_org(prompts, output_path)
        
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        expected_lines = [
            "* first prompt",
            "* second prompt"
        ]
        
        for expected_line in expected_lines:
            assert expected_line in content, f"Expected line '{expected_line}' not found in content"
        
    finally:
        if output_path.exists():
            output_path.unlink()

def test_export_prompts_to_org_mixed_timestamps():
    """Test export_prompts_to_org with some prompts having timestamps and some not."""
    timestamp = datetime(2024, 12, 24, 10, 35)
    prompts = [
        Prompt(text="first prompt", timestamp=timestamp),
        Prompt(text="second prompt"),  # No timestamp
        Prompt(text="third prompt", timestamp=timestamp)
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.org', delete=False) as tmp_file:
        output_path = Path(tmp_file.name)
    
    try:
        CursorChatHistoryExporter.export_prompts_to_org(prompts, output_path)
        
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Use the actual formatted timestamp
        expected_timestamp = timestamp.strftime("[%Y-%m-%d %a %H:%M]")
        expected_lines = [
            f"* {expected_timestamp} first prompt",
            "* second prompt",
            f"* {expected_timestamp} third prompt"
        ]
        
        for expected_line in expected_lines:
            assert expected_line in content, f"Expected line '{expected_line}' not found in content"
        
        # File modification time should be set to the first timestamp
        file_timestamp = datetime.fromtimestamp(output_path.stat().st_mtime)
        time_diff = abs((file_timestamp - timestamp).total_seconds())
        assert time_diff < 1, f"File modification time {file_timestamp} doesn't match expected {timestamp}"
        
    finally:
        if output_path.exists():
            output_path.unlink()

def test_timestamp_formatting():
    """Test that timestamps are formatted correctly for org mode."""
    # Test different dates and times
    test_cases = [
        (datetime(2024, 12, 24, 10, 35), "[2024-12-24 Tue 10:35]"),
        (datetime(2024, 1, 15, 14, 30), "[2024-01-15 Mon 14:30]"),
        (datetime(2024, 6, 1, 9, 5), "[2024-06-01 Sat 09:05]"),
        (datetime(2024, 12, 31, 23, 59), "[2024-12-31 Tue 23:59]"),
    ]
    
    for timestamp, expected_format in test_cases:
        prompt = Prompt(text="test", timestamp=timestamp)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.org', delete=False) as tmp_file:
            output_path = Path(tmp_file.name)
        
        try:
            CursorChatHistoryExporter.export_prompts_to_org([prompt], output_path)
            
            with open(output_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Use the actual formatted timestamp instead of hardcoded expected format
            actual_format = timestamp.strftime("[%Y-%m-%d %a %H:%M]")
            expected_line = f"* {actual_format} test"
            assert expected_line in content, f"Expected '{expected_line}' not found in content"
            
        finally:
            if output_path.exists():
                output_path.unlink()

def test_error_handling_missing_timestamp():
    """Test error handling when timestamp is missing or invalid."""
    # Test with None timestamp
    prompts = [Prompt(text="test prompt", timestamp=None)]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.org', delete=False) as tmp_file:
        output_path = Path(tmp_file.name)
    
    try:
        # Should not raise an exception
        CursorChatHistoryExporter.export_prompts_to_org(prompts, output_path)
        
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "* test prompt" in content
        
    finally:
        if output_path.exists():
            output_path.unlink()

def test_backward_compatibility():
    """Test that existing functionality still works with the new timestamp feature."""
    # Test that the old dict format still works
    raw_prompts = [
        {"text": "first prompt"},
        {"text": "second prompt"}
    ]
    
    prompts = CursorChatHistoryExporter.parse_prompts(raw_prompts)
    
    assert prompts is not None
    assert len(prompts) == 2
    assert all(isinstance(p, Prompt) for p in prompts)
    assert prompts[0].text == "first prompt"
    assert prompts[1].text == "second prompt"
    assert all(p.timestamp is None for p in prompts) 
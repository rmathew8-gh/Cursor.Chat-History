from pathlib import Path
from cursor_chat_history import extract_ai_service_prompts

def test_extract_ai_service_prompts():
    db_path = Path(__file__).parent / "state_example.vscdb"
    prompts = extract_ai_service_prompts(db_path)
    assert prompts is not None, "No prompts returned from extract_ai_service_prompts"
    assert isinstance(prompts, list), "Returned prompts is not a list"
    assert len(prompts) > 0, "No prompts found in the .vscdb file"
    for prompt in prompts:
        assert 'text' in prompt, "Prompt entry missing 'text' field" 
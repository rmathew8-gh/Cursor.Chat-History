# Makefile for cursor_chat_history Python project

# Install dependencies using uv
install:
	uv pip install -e .

# Run the main script
run:
	uv run python cursor_chat_history.py

# Lint the code using ruff
lint:
	uv run ruff .

# Run unit tests with pytest
test:
	PYTHONPATH=. uv run pytest tests/

# Clean up cache and export directories, and auto-fix lint
clean:
	rm -rf __pycache__ .ruff_cache chat_history_exports
	uv run ruff check --fix .

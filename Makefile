# Makefile for cursor_chat_history Python project

# Install dependencies using uv
install:
	uv pip install -r requirements.txt

# Run the main script
run:
	uv pip install -e .
	python cursor_chat_history.py

# Lint the code using ruff
lint:
	ruff .

# Run unit tests with pytest
test:
	uv pip install pytest && pytest tests/

# Clean up cache and export directories
clean:
	rm -rf __pycache__ .ruff_cache chat_history_exports 
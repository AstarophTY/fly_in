TEMP_FILE := *.egg-info build dist .pytest_cache .mypy_cache
MYPY_FLAG := --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs
UV := uv

all: run

run: install
	$(UV) run python main.py

install:
	$(UV) sync

clean:
	@$(RM) -rf $(TEMP_FILE)
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type f -name "*.py[co]" -delete

benchmark: install
	$(UV) run python benchmark.py

debug:
	$(UV) run python -m pdb -m src

lint:
	$(UV) run flake8 *.py
	$(UV) run mypy *.py $(MYPY_FLAG)

lint-strict:
	$(UV) run flake8 *.py
	$(UV) run mypy *.py --strict
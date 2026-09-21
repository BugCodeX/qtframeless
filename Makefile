.PHONY: help install install-dev lint format type-check test test-cov pre-commit-install pre-commit-run

UV := uv
# =======================================================================
# Help
# =======================================================================
help:
	@echo "Development:"
	@echo "    make install          Install production dependencies"
	@echo "    make install-dev      Install all dev dependencies"
	@echo ""
	@echo "Tests:"
	@echo "    make test             Execute tests using pytest"
	@echo "    make test-cov         Run pytest with coverage reporting"
	@echo ""
	@echo "Quality:"
	@echo "    make lint             Check code style using ruff"
	@echo "    make format           Format code using ruff"
	@echo "    make type-check       Check types using pyright"
	@echo ""

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

install:
	$(UV) sync --all-packages --no-dev

install-dev:
	$(UV) sync --all-packages

sync:
	$(UV) sync --all-packages

pre-commit-install:
	$(UV) run pre-commit install --hook-type pre-commit --hook-type commit-msg

pre-commit-run:
	$(UV) run pre-commit run --all-files

# ---------------------------------------------------------------------------
# Quality
# ---------------------------------------------------------------------------

lint:
	$(UV) run ruff check .

format:
	$(UV) run ruff format .
	$(UV) run ruff check --fix .

type-check:
	$(UV) run pyright

type-check-json:
	$(UV) run pyright --outputjson

# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

test:
	$(UV) run pytest

test-cov:
	$(UV) run pytest --cov=qtframeless --cov-report=term-missing --cov-report=html

# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------

clean:
	$(UV) run python -c "import shutil, pathlib; [shutil.rmtree(p, ignore_errors=True) for p in ['dist','site','htmlcov','.pytest_cache','.ruff_cache']]; [shutil.rmtree(p, ignore_errors=True) for p in pathlib.Path('.').rglob('__pycache__')]; [shutil.rmtree(p, ignore_errors=True) for p in pathlib.Path('.').rglob('*.egg-info')]"

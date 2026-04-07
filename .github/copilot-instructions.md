# Copilot Instructions - Corpus Preparation

## Project Overview
Peralatan untuk persiapan dan penyiapan data corpus (dataset) dengan Python 3.11.

## Environment Setup

### Python & Virtual Environment
- **Python Version:** 3.11.15 (managed by pyenv)
- **Virtual Environment:** `venv/` folder
- **Activation:** `source venv/bin/activate`
- **PyPI:** Uses pip for package management

### Quick Setup
```bash
cd corpus-preparation
source venv/bin/activate
```

## Build, Test & Development Commands

### Dependencies
```bash
pip install -r requirements.txt      # Install dependencies
pip install -r requirements-dev.txt  # Install dev dependencies (if exists)
```

### Running Code
```bash
python -m main                       # Run main module (example)
python script.py                     # Run specific script
```

### Testing
```bash
pytest                              # Run all tests
pytest -v                           # Verbose output
pytest tests/test_module.py         # Run specific test file
pytest -k test_function             # Run specific test by name
```

### Code Quality
```bash
black .                             # Format code
flake8 .                            # Lint code
mypy .                              # Type checking (if configured)
```

## Architecture

### Directory Structure
```
corpus-preparation/
├── venv/                    # Virtual environment
├── .github/
│   └── copilot-instructions.md
├── .env.example             # Environment variables template
├── .python-version          # Python version for pyenv
├── requirements.txt         # Production dependencies
├── requirements-dev.txt     # Development dependencies (if exists)
└── src/                     # Main source code (typical structure)
```

### Key Conventions
- Use `src/` or `corpus_preparation/` for main code
- Test files go in `tests/` directory
- Configuration in `.env` (copy from `.env.example`)
- Always use virtual environment before installing packages

## Important Notes

- **Do NOT commit** `venv/` folder - it's in .gitignore
- **Do NOT commit** `.env` file with sensitive data
- **Python 3.11** is locked in `.python-version`
- Always activate venv before working: `source venv/bin/activate`

## Common Workflows

### Adding a New Dependency
```bash
source venv/bin/activate
pip install package-name
pip freeze > requirements.txt
```

### Running a Specific Task
1. Activate venv
2. Check available commands in Makefile (if exists)
3. Run scripts directly with `python`

---
Last Updated: 2026-04-07

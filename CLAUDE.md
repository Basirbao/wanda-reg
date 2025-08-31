# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture Overview

This is a Python automation tool with a modular service-oriented architecture:

- `main.py` - Application entry point and orchestration loop
- `test_workflow.py` - Testing workflow for registration process
- `services/` - Core business logic services
  - `registration_service.py` - Main orchestration service (RegistrationOrchestrator)
  - `browser_service.py` - Browser automation using Playwright
  - `mail_service.py` - Email service integration with Mail.tm API
- `utils/` - Shared utilities
  - `logger.py` - Centralized logging setup
  - `password_generator.py` - Password generation utilities
- `config/` - Configuration management
  - `settings.py` - Environment-based configuration with .env support

## Development Setup and Commands

### Environment Setup
```bash
# Create UV virtual environment and install dependencies
./run.sh

# Or manual setup:
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
playwright install chromium
```

### Running the Application
```bash
# Run with UV environment setup
./run.sh

# Or manual execution:
source .venv/bin/activate
python main.py

# For headless environments (using xvfb):
xvfb-run python main.py
```

### Testing
```bash
# Test registration workflow (non-headless for observation)
python test_workflow.py
```

### Configuration
- Copy `.env.example` to `.env` and configure required settings
- Key configuration options in `config/settings.py`:
  - `REGISTRATION_COUNT` - Number of registration attempts
  - `HEADLESS_MODE` - Browser visibility mode
  - `PROXY_URL` - Optional proxy configuration
  - `MAIL_TM_API_URL` - Email service endpoint

## Dependencies

The project uses UV for dependency management with these core packages:
- `playwright` - Browser automation
- `requests` - HTTP client
- `python-dotenv` - Environment variable management

## Key Design Patterns

- Service orchestration pattern with `RegistrationOrchestrator` as the main coordinator
- Environment-based configuration with fallback defaults
- Structured logging throughout all services
- Resource management with proper browser cleanup in finally blocks
- Retry logic and error handling in service operations
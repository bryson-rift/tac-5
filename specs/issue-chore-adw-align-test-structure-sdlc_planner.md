# Chore: Align test structure with original ADW philosophy

## Chore Description
Refactor the test infrastructure to follow the ADW (AI Developer Workflow) self-contained philosophy by removing external test framework dependencies (pytest) and converting all test files to standalone scripts that can be executed directly with `uv run`. Each test file should be self-contained with inline dependencies, clear console output with pass/fail indicators, and proper exit codes for CI/CD integration. This maintains the ADW principle where every script is independent and can run without external configuration or framework setup.

## Relevant Files
Use these files to resolve the chore:

- `run_tests.py` - Root-level pytest runner that needs to be removed (uses pytest.main())
- `adws/adw_tests/test_webhook_ngrok.py` - Test file using pytest that needs to be refactored to standalone format (361 lines with class-based tests and pytest decorators)
- `adws/adw_tests/test_agents.py` - Reference implementation showing the correct standalone pattern (132 lines, clean structure)
- `adws/adw_plan_build_test.py` - Reference implementation of workflow script pattern (86 lines, clean)
- `adws/adw_tests/test_e2e_generate_query.py` - E2E test file that needs shebang and inline dependencies added

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Remove pytest infrastructure files
- Delete the `run_tests.py` file from the project root
- Check if `pyproject.toml` exists and delete it if present

### 2. Add shebang and inline dependencies to test_e2e_generate_query.py
- Add shebang line: `#!/usr/bin/env -S uv run`
- Add inline script dependencies header with playwright and other required packages
- Ensure it can be run directly with `uv run`

### 3. Refactor test_webhook_ngrok.py - Remove pytest imports
- Remove all pytest imports (`import pytest`, `from unittest.mock import`)
- Remove dotenv and other imports that will be handled inline
- Keep only standard library imports plus inline dependencies

### 4. Refactor test_webhook_ngrok.py - Convert classes to functions
- Convert `TestEnvironmentConfiguration` class methods to standalone functions:
  - `test_env_file_exists()` → `check_env_file_exists()`
  - `test_required_env_vars()` → `check_required_env_vars()`
  - `test_ngrok_authtoken()` → `check_ngrok_authtoken()`
- Convert `TestNgrokIntegration` class methods to standalone functions:
  - `test_ngrok_installed()` → `check_ngrok_installed()`
  - `test_ngrok_config()` → `check_ngrok_config()`
  - `test_ngrok_tunnel_creation()` → `check_ngrok_tunnel_creation()`
- Convert `TestWebhookServer` class methods to standalone functions:
  - Remove `webhook_url` fixture and use a constant or function parameter
  - `test_webhook_health_endpoint()` → `check_webhook_health_endpoint()`
  - `test_webhook_status_endpoint()` → `check_webhook_status_endpoint()`
  - `test_webhook_accepts_github_events()` → `check_webhook_accepts_github_events()`
  - `test_webhook_detects_adw_workflow()` → `check_webhook_detects_adw_workflow()`
- Convert `TestWebhookAutoConfiguration` class methods to standalone functions
- Convert `TestEndToEndWorkflow` class methods to standalone functions
- Keep the existing `test_integration_suite_health()` function as-is but rename to `check_integration_suite_health()`

### 5. Refactor test_webhook_ngrok.py - Replace pytest features
- Replace all `pytest.fail()` calls with `print()` and `return False`
- Replace all `pytest.skip()` calls with `print("Skipping: reason")` and `return True`
- Replace all `assert` statements with conditional checks that print error messages and return False
- Replace `@pytest.fixture` decorators by converting fixtures to regular functions or constants
- Replace `@pytest.mark.skipif` decorators with conditional logic inside the function

### 6. Refactor test_webhook_ngrok.py - Add main() function
- Create a `main()` function that runs all test functions sequentially
- Track success/failure for each test
- Print results with ✅/❌ indicators
- Return overall success status
- Add proper exit code handling (sys.exit(0) for success, sys.exit(1) for failure)

### 7. Refactor test_webhook_ngrok.py - Update file structure
- Add shebang: `#!/usr/bin/env -S uv run`
- Add inline dependencies in script header (requests, python-dotenv, pydantic)
- Update docstring to reflect standalone execution
- Add `if __name__ == "__main__": main()` at the bottom

### 8. Validate the refactored test files
- Run the refactored test_webhook_ngrok.py to ensure it works: `uv run adws/adw_tests/test_webhook_ngrok.py`
- Run test_agents.py to ensure it still works: `uv run adws/adw_tests/test_agents.py`
- Run test_e2e_generate_query.py to ensure it works with new structure: `uv run adws/adw_tests/test_e2e_generate_query.py`
- Verify proper exit codes are returned (echo $? after each run)
- Ensure clear console output with pass/fail indicators

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `ls run_tests.py 2>/dev/null || echo "✅ run_tests.py removed successfully"` - Verify run_tests.py is removed
- `ls pyproject.toml 2>/dev/null || echo "✅ pyproject.toml not present"` - Verify pyproject.toml is removed if it existed
- `head -n 1 adws/adw_tests/test_webhook_ngrok.py | grep -q "#!/usr/bin/env -S uv run" && echo "✅ Shebang present" || echo "❌ Shebang missing"` - Verify shebang is present
- `grep -q "import pytest" adws/adw_tests/test_webhook_ngrok.py && echo "❌ pytest imports still present" || echo "✅ pytest imports removed"` - Verify no pytest imports
- `grep -q "class Test" adws/adw_tests/test_webhook_ngrok.py && echo "❌ Test classes still present" || echo "✅ Classes converted to functions"` - Verify no test classes
- `uv run adws/adw_tests/test_webhook_ngrok.py` - Run refactored webhook test
- `uv run adws/adw_tests/test_agents.py` - Run agents test to ensure no regression
- `uv run adws/adw_tests/test_e2e_generate_query.py || echo "Note: E2E test requires browser and running app"` - Run E2E test (may skip if dependencies not met)

## Notes
- The goal is to maintain all test coverage while removing framework dependencies
- Each test file should be completely self-contained and runnable independently
- Test output should be clear and human-readable with visual indicators
- Exit codes must be reliable for CI/CD integration (0 = success, 1 = failure)
- Follow the patterns established in test_agents.py for consistency
- Preserve all test logic - only change the structure and execution method
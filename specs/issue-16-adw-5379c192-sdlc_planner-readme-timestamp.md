# Feature: README.md Timestamp Tracker

## Feature Description
A bash script that automatically appends a timestamp line to README.md (or any specified file) to track when documentation was last updated. This provides visibility into documentation freshness and helps maintain up-to-date project information. The script follows existing patterns in the scripts/ directory and integrates seamlessly with the project's tooling.

## User Story
As a developer or project maintainer
I want to automatically append a timestamp to README.md
So that I can track when the documentation was last updated without manual effort

## Problem Statement
There is currently no automated way to track when README.md or other documentation files were last updated. Manual timestamp tracking is error-prone and often forgotten, making it difficult for users and contributors to know if they're viewing current information.

## Solution Statement
Create a reusable bash script (`scripts/readme-timestamp.sh`) that appends a formatted timestamp line to the end of README.md (or any file passed as an argument). The script will use Pacific Time formatting, be executable, follow existing script conventions (colored output, error handling), and be simple enough to integrate into git hooks or manual workflows.

## Relevant Files
Use these files to implement the feature:

- `scripts/start.sh` - Reference for script structure, colored output patterns, error handling, and script directory resolution
- `scripts/stop_apps.sh` - Reference for simple script format with colored output
- `scripts/copy_dot_env.sh` - Reference for file operations and error handling patterns
- `scripts/reset_db.sh` - Likely contains simple file/database reset operations (inspect for patterns)
- `README.md` - The default target file that will receive timestamp updates

### New Files
- `scripts/readme-timestamp.sh` - The new script that appends timestamps to files

## Implementation Plan

### Phase 1: Foundation
Research existing script patterns in the codebase to ensure consistency. Examine:
- How scripts handle colored output (GREEN, BLUE, RED, NC variables)
- Error handling approaches (exit codes, conditional checks)
- Path resolution methods (SCRIPT_DIR, PROJECT_ROOT patterns)
- Script headers and structure (shebang, comments)

### Phase 2: Core Implementation
Create the `scripts/readme-timestamp.sh` script with the following functionality:
- Accept optional filename argument (default: README.md)
- Generate Pacific Time timestamp in format: "Last updated: 2025-10-08 12:34:56"
- Append timestamp line to the target file
- Provide colored output for success/error states
- Handle edge cases (file doesn't exist, no write permissions)
- Make script executable with proper permissions

### Phase 3: Integration
- Test the script with README.md as the default target
- Test with alternative files passed as arguments
- Verify the script works from different working directories
- Validate timestamp formatting is correct for Pacific Time
- Ensure the script follows existing patterns and conventions

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Inspect existing script patterns
- Read `scripts/reset_db.sh` to understand any additional patterns not yet examined
- Document the common patterns for error handling, colored output, and file operations
- Note the typical script structure and conventions used across the codebase

### Step 2: Create the timestamp script
- Create `scripts/readme-timestamp.sh` with the following features:
  - Proper bash shebang and header comments
  - Colored output variables (GREEN, BLUE, RED, NC)
  - Accept optional filename argument (default to README.md)
  - Generate Pacific Time timestamp using `TZ='America/Los_Angeles' date '+%Y-%m-%d %H:%M:%S'`
  - Append formatted line: "Last updated: YYYY-MM-DD HH:MM:SS"
  - Validate file exists before appending
  - Handle write permission errors gracefully
  - Output success/error messages with appropriate colors
- Make the script executable: `chmod +x scripts/readme-timestamp.sh`

### Step 3: Create unit tests
- Create test script `scripts/test_readme_timestamp.sh` to validate:
  - Default behavior (no arguments, uses README.md)
  - Custom file argument behavior
  - Error handling when file doesn't exist
  - Error handling for permission issues
  - Timestamp format validation
  - Pacific Time zone correctness

### Step 4: Test the implementation
- Run the script with default argument: `./scripts/readme-timestamp.sh`
- Verify README.md has new timestamp line appended
- Run with custom file: `./scripts/readme-timestamp.sh test-file.txt`
- Test error cases (non-existent file, read-only file)
- Verify timestamps are in Pacific Time
- Verify multiple runs append multiple timestamps correctly

### Step 5: Run validation commands
- Execute all commands in the `Validation Commands` section
- Ensure zero errors and all tests pass
- Verify the script works as expected in all scenarios

## Testing Strategy

### Unit Tests
Create a test script (`scripts/test_readme_timestamp.sh`) that validates:
1. **Default behavior**: Script appends to README.md when no argument provided
2. **Custom file argument**: Script appends to specified file when argument provided
3. **File existence check**: Script fails gracefully when target file doesn't exist
4. **Permission handling**: Script reports error when file isn't writable
5. **Timestamp format**: Timestamp matches expected format "YYYY-MM-DD HH:MM:SS"
6. **Pacific Time**: Timestamp is in Pacific Time zone
7. **Multiple runs**: Multiple executions append multiple timestamp lines

### Edge Cases
- Target file doesn't exist (should report error)
- Target file is read-only (should report permission error)
- No filename argument provided (should default to README.md)
- Running from different working directories
- File path with spaces in filename
- Empty file vs file with content

## Acceptance Criteria
1. ✅ Script exists at `scripts/readme-timestamp.sh`
2. ✅ Script is executable (`chmod +x` applied)
3. ✅ Script appends timestamp in format: "Last updated: YYYY-MM-DD HH:MM:SS"
4. ✅ Timestamp uses Pacific Time zone
5. ✅ Script accepts optional filename argument
6. ✅ Script defaults to README.md when no argument provided
7. ✅ Script follows existing patterns (colored output, error handling)
8. ✅ Script handles errors gracefully (missing file, permissions)
9. ✅ Test script validates all functionality
10. ✅ All validation commands pass without errors

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `./scripts/readme-timestamp.sh` - Run script with default argument (README.md)
- `cat README.md | tail -5` - Verify timestamp was appended to README.md
- `./scripts/test_readme_timestamp.sh` - Run unit tests to validate all functionality
- `cd app/server && uv run pytest` - Run server tests to validate the feature works with zero regressions
- `cd app/client && bun tsc --noEmit` - Run frontend tests to validate the feature works with zero regressions
- `cd app/client && bun run build` - Run frontend build to validate the feature works with zero regressions

## Notes

### Script Design Decisions
- **Pacific Time Format**: Uses `TZ='America/Los_Angeles'` environment variable with `date` command for timezone specification
- **Append vs Replace**: Script appends timestamps to track update history rather than replacing previous timestamps
- **Error Handling**: Follows existing patterns with colored output and non-zero exit codes
- **File Argument**: Supports optional filename argument for flexibility beyond README.md

### Future Enhancements
- Consider adding `--replace` flag to replace last timestamp instead of appending
- Could integrate with git pre-commit hooks to auto-update on commits
- Might add `--quiet` flag to suppress output for automation scenarios
- Could support timestamp format customization via arguments

### Testing Notes
- The test script should create temporary test files to avoid modifying real files during testing
- Test isolation is important - each test should clean up after itself
- Consider testing with `set -e` to ensure script exits on errors as expected

# Feature: README.md Timestamp Script

## Feature Description
Create a bash script that automatically appends a timestamp to the end of README.md (or any specified file) to track when documentation was last updated. The script will be located at `scripts/readme-timestamp.sh`, follow existing script patterns in the codebase, and provide flexible filename support through optional arguments.

## User Story
As a developer maintaining documentation
I want to automatically append timestamps to README.md whenever it's updated
So that team members and users can quickly see when the documentation was last modified

## Problem Statement
Currently, there is no automated way to track when README.md or other documentation files are updated. This makes it difficult for users and contributors to know if they're reading current information, and there's no consistent way to mark documentation updates across the project.

## Solution Statement
Implement a bash script at `scripts/readme-timestamp.sh` that:
- Appends a formatted timestamp line to the end of a file
- Defaults to README.md but accepts any filename as an argument
- Uses Pacific Time zone for consistency
- Follows the existing script patterns (shebang, executable permissions, error handling, color output)
- Can be easily integrated into development workflows or CI/CD pipelines

## Relevant Files
Use these files to implement the feature:

- `README.md` - The default target file that will receive timestamp updates
- `scripts/start.sh` - Reference for script structure, color output patterns, and error handling
- `scripts/stop_apps.sh` - Reference for consistent script formatting and messaging patterns
- `scripts/reset_db.sh` - Reference for simple script operations with success/failure reporting
- `scripts/copy_dot_env.sh` - Reference for file operations and path handling

### New Files
- `scripts/readme-timestamp.sh` - The main script that appends timestamps to files

## Implementation Plan
### Phase 1: Foundation
Create the basic script structure following existing patterns:
- Set up proper shebang and script header
- Define color constants for output (GREEN, BLUE, RED, NC) matching existing scripts
- Implement argument parsing for optional filename parameter
- Set default filename to README.md

### Phase 2: Core Implementation
Implement the timestamp appending logic:
- Get the current date/time in Pacific Time zone
- Format the timestamp string as "Last updated: YYYY-MM-DD HH:MM:SS"
- Validate that the target file exists
- Append the timestamp line to the end of the file
- Provide clear success/error messages with color coding

### Phase 3: Integration
Finalize the script and ensure it meets requirements:
- Make the script executable (chmod +x)
- Add comprehensive error handling for edge cases
- Test with both default (README.md) and custom filename arguments
- Ensure the script follows project conventions
- Update documentation if needed

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Create the readme-timestamp.sh script
- Create `scripts/readme-timestamp.sh` with proper shebang (`#!/bin/bash`)
- Add color constants matching existing scripts (GREEN, BLUE, RED, NC)
- Implement argument parsing to accept optional filename parameter (default: README.md)
- Add validation to check if target file exists
- Implement timestamp generation using Pacific Time zone
- Add logic to append "Last updated: YYYY-MM-DD HH:MM:SS" to the end of the target file
- Include clear, colorized output messages for success and error cases
- Follow the coding style and patterns from existing scripts (start.sh, stop_apps.sh, reset_db.sh)

### Step 2: Make the script executable
- Run `chmod +x scripts/readme-timestamp.sh` to make the script executable
- Verify the script has proper executable permissions

### Step 3: Test the script with default behavior
- Run `./scripts/readme-timestamp.sh` to test with default README.md
- Verify a timestamp line is appended to README.md
- Confirm the timestamp format matches requirements
- Verify Pacific Time is used correctly

### Step 4: Test the script with custom filename
- Create a test file to use as an argument
- Run `./scripts/readme-timestamp.sh <test-file>` to test with custom filename
- Verify the timestamp is appended to the specified file
- Clean up test file after verification

### Step 5: Test error handling
- Test running the script on a non-existent file
- Verify appropriate error messages are displayed
- Confirm the script exits with proper error codes

### Step 6: Run validation commands
- Execute all commands in the `Validation Commands` section
- Ensure all tests pass with zero regressions
- Verify the script works correctly in all scenarios

## Testing Strategy
### Unit Tests
Since this is a bash script, testing will be done through manual execution and validation:
- Test default behavior (no arguments, uses README.md)
- Test with custom filename argument
- Test with non-existent file (should fail gracefully)
- Test timestamp format and timezone correctness
- Verify executable permissions are set correctly

### Edge Cases
- Non-existent file path: Should display error and exit with non-zero code
- File without write permissions: Should fail with appropriate error message
- Empty filename argument: Should fall back to default README.md
- Script run multiple times: Should append multiple timestamps (not replace)
- File with special characters in name: Should handle properly
- Relative vs absolute paths: Should work with both

## Acceptance Criteria
- [ ] Script exists at `scripts/readme-timestamp.sh`
- [ ] Script is executable (chmod +x)
- [ ] Default behavior appends timestamp to README.md
- [ ] Accepts optional filename argument
- [ ] Timestamp format is "Last updated: YYYY-MM-DD HH:MM:SS"
- [ ] Uses Pacific Time zone (not UTC or other zones)
- [ ] Follows existing script patterns (colors, error handling, output style)
- [ ] Provides clear success/error messages
- [ ] Handles non-existent files gracefully with error messages
- [ ] Can be run multiple times without errors

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `ls -la scripts/readme-timestamp.sh` - Verify the script exists and is executable
- `./scripts/readme-timestamp.sh` - Run script with default README.md to verify it works
- `tail -n 5 README.md` - Verify timestamp was appended to README.md
- `touch /tmp/test-timestamp.txt && ./scripts/readme-timestamp.sh /tmp/test-timestamp.txt && cat /tmp/test-timestamp.txt` - Test with custom filename
- `./scripts/readme-timestamp.sh /nonexistent/file.txt` - Test error handling for non-existent file (should fail gracefully)
- `cd app/server && uv run pytest` - Run server tests to validate the feature works with zero regressions
- `cd app/client && bun tsc --noEmit` - Run frontend tests to validate the feature works with zero regressions
- `cd app/client && bun run build` - Run frontend build to validate the feature works with zero regressions

## Notes
- This feature is a standalone utility script and does not affect the main application code
- The script uses Pacific Time zone as specified in requirements, which requires proper TZ environment variable handling
- The script can be integrated into CI/CD workflows or git hooks for automated documentation timestamping
- Consider documenting the script usage in README.md after implementation
- The timestamp format is consistent and machine-readable while remaining human-friendly
- Script follows defensive programming practices with input validation and error handling
- No external dependencies required beyond standard bash utilities (date, echo)
- The script uses `>>` append operation, not overwrite, so multiple runs add multiple timestamps

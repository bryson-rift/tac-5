# Feature: Query Variety for Generate Test Query Button

## Feature Description
Enhance the Generate Test Query button to produce varied, non-repetitive queries when clicked multiple times. Currently, the LLM generates identical queries on successive clicks even with temperature=0.7, failing the E2E test requirement for query variety. This feature will implement a variety mechanism that ensures each generated query explores different aspects of the database schema.

## User Story
As a user of the Natural Language SQL Interface
I want the Generate Test Query button to produce different queries each time I click it
So that I can explore various aspects of my data and test different query patterns without repetition

## Problem Statement
The E2E test for the Generate Test Query button failed at step 21 with the error: "Second query is identical to first query, expected variety". Despite using temperature=0.7 in the LLM calls, the system generates identical queries on successive clicks because:
1. No query history tracking exists to prevent repetition
2. No explicit variety instructions are provided to the LLM
3. No query category/pattern rotation mechanism guides the generation

## Solution Statement
Implement a multi-layered approach to ensure query variety:
1. Track recently generated queries in memory to detect and prevent exact duplicates
2. Add explicit variety instructions to the LLM prompt including the last generated query
3. Implement query category rotation (e.g., simple filters, aggregations, joins, sorting) to guide varied query patterns
4. Increase temperature to 0.9 for more creative outputs
5. Add retry logic to regenerate if duplicate detected (max 3 attempts)

## Relevant Files
Use these files to implement the feature:

- `app/server/core/llm_processor.py` - Contains `generate_test_query_with_openai()` and `generate_test_query_with_anthropic()` functions that need variety mechanisms
- `app/server/server.py` - Contains `/api/generate-query` endpoint that will track query history in memory
- `app/server/core/data_models.py` - May need new data models for tracking query history
- `app/server/tests/test_generate_query.py` - Unit tests for the generate query functionality that need updating
- `.claude/commands/e2e/test_generate_query.md` - E2E test that validates query variety (already exists)

### New Files
No new files are required for this feature.

## Implementation Plan

### Phase 1: Foundation
Add query history tracking mechanism to the backend server to store recently generated queries in memory. This will enable duplicate detection and provide context to the LLM for generating varied queries.

### Phase 2: Core Implementation
Enhance the LLM prompt with explicit variety instructions, query categories, and context about previously generated queries. Increase temperature for more creative outputs and implement retry logic to handle duplicates.

### Phase 3: Integration
Update the API endpoint to manage query history, validate variety requirements, and ensure the E2E test passes with diverse query generation.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Add query history tracking to server
- Modify `app/server/server.py` to add a global in-memory query history cache
- Use a deque with maxlen=10 to store the last 10 generated queries per session
- Import `from collections import deque` at the top of the file
- Initialize the query history cache as `query_history = deque(maxlen=10)` below the `app_start_time` line

### Step 2: Define query categories for variety
- Modify `app/server/core/llm_processor.py` to add a list of query categories
- Add after the imports: `QUERY_CATEGORIES = ["simple filters", "aggregations and counts", "sorting and limits", "comparisons and ranges", "multiple columns"]`
- These categories will guide the LLM to generate different types of queries

### Step 3: Enhance OpenAI query generation with variety
- Modify `generate_test_query_with_openai()` in `app/server/core/llm_processor.py`
- Add parameters: `recent_queries: list[str] = None, preferred_category: str = None`
- Increase temperature from 0.7 to 0.9
- Update the prompt to include:
  - "IMPORTANT: Generate a DIFFERENT query from these recent ones: {recent_queries}" if recent_queries is provided
  - "Focus on {preferred_category} type queries" if preferred_category is provided
  - Add example query patterns for each category
- Keep existing 2-sentence limit and safety requirements

### Step 4: Enhance Anthropic query generation with variety
- Modify `generate_test_query_with_anthropic()` in `app/server/core/llm_processor.py`
- Add the same parameters: `recent_queries: list[str] = None, preferred_category: str = None`
- Increase temperature from 0.7 to 0.9
- Apply the same prompt enhancements as OpenAI version
- Ensure consistency between both provider implementations

### Step 5: Update main generate_test_query function
- Modify `generate_test_query()` in `app/server/core/llm_processor.py`
- Add parameters: `recent_queries: list[str] = None, preferred_category: str = None`
- Pass these parameters to both OpenAI and Anthropic functions
- Add retry logic: attempt generation up to 3 times if duplicate is detected
- Return the first non-duplicate query or the third attempt

### Step 6: Update API endpoint with query history
- Modify `/api/generate-query` endpoint in `app/server/server.py`
- Access the global `query_history` deque
- Convert deque to list and pass as `recent_queries` to `generate_test_query()`
- Implement category rotation: use `len(query_history) % len(QUERY_CATEGORIES)` to cycle through categories
- After successful generation, add the new query to `query_history`
- Ensure thread-safe access if needed (not critical for single-process dev setup)

### Step 7: Update unit tests
- Modify `app/server/tests/test_generate_query.py`
- Update existing tests to handle new optional parameters
- Add new test: `test_generate_query_with_variety()` that generates 3 queries and asserts they are all different
- Add new test: `test_generate_query_with_recent_queries()` that passes recent queries and verifies the new query is different
- Add new test: `test_generate_query_with_category()` that verifies category-specific queries are generated
- Ensure all tests mock the LLM API calls properly

### Step 8: Run validation commands
- Execute all validation commands listed below to ensure zero regressions
- Verify the E2E test passes with query variety
- Fix any issues that arise

## Testing Strategy

### Unit Tests
- Test query generation with empty query history
- Test query generation with populated query history (duplicate detection)
- Test query generation with different categories
- Test retry logic when duplicates are generated
- Test query history deque behavior (maxlen=10)
- Mock LLM API responses to ensure deterministic testing

### Edge Cases
- No tables in database (existing error handling should work)
- Query history full (10 queries) - should use deque rotation
- LLM generates duplicate after 3 retries - should return the third attempt
- Invalid category provided - should generate without category guidance
- Empty recent_queries list - should work normally
- Query history contains queries from different table schemas - should still work

## Acceptance Criteria
- Generate Test Query button produces different queries on successive clicks (E2E test step 21 passes)
- Query variety is achieved through category rotation and duplicate prevention
- Recently generated queries (last 10) are tracked in memory
- LLM prompts include context about recent queries to avoid repetition
- Temperature is increased to 0.9 for more creative outputs
- Retry logic attempts up to 3 times to avoid duplicates
- All existing functionality remains unchanged
- All unit tests pass
- E2E test `.claude/commands/e2e/test_generate_query.md` passes completely
- Query generation still respects 2-sentence limit and safety requirements

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `cd app/server && uv run python -m py_compile server.py core/llm_processor.py core/data_models.py` - Validate Python syntax
- `cd app/server && uv run ruff check .` - Run linting to catch code quality issues
- `cd app/server && uv run pytest tests/test_generate_query.py -v` - Run generate query unit tests
- `cd app/server && uv run pytest tests/ -v --tb=short` - Run all backend tests to validate zero regressions
- `cd app/client && bun tsc --noEmit` - Run TypeScript type checking (no client changes expected)
- `cd app/client && bun run build` - Run frontend build to validate no regressions
- Read `.claude/commands/test_e2e.md`, then read and execute `.claude/commands/e2e/test_generate_query.md` to validate query variety works end-to-end

## Notes
- The in-memory query history will reset when the server restarts, which is acceptable for this use case
- Consider using session-based query history in the future for multi-user scenarios
- The category rotation ensures variety even if the LLM has a bias toward certain query types
- Temperature of 0.9 provides good variety while maintaining coherent queries
- The 3-retry limit prevents infinite loops while giving the LLM multiple chances to generate unique queries
- This implementation is stateless and thread-safe for single-process development setups
- Future enhancement: persist query history to database for cross-session variety
- Future enhancement: add user preferences for query complexity levels

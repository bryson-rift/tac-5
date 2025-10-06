# Feature: Generate Test Query Button

## Feature Description
Add a "Generate Test Query" button to the Natural Language SQL Interface that uses AI to automatically generate interesting natural language queries based on the current database schema and available tables. The button will be positioned between the existing "Query" and "Upload Data" buttons, styled in bright red with an animation during LLM processing, and will populate the query input field with AI-generated queries that users can execute immediately.

## User Story
As a user of the Natural Language SQL Interface
I want a button that automatically generates example queries for my database
So that I can quickly test the system's capabilities and explore my data without having to think of queries myself

## Problem Statement
Users who upload data to the Natural Language SQL Interface may not immediately know what questions to ask or how to phrase their queries effectively. This creates friction in the user experience and may prevent users from fully exploring the application's capabilities. Currently, users must manually type queries, which requires:
1. Understanding what data is available in their tables
2. Formulating natural language questions
3. Knowing what types of queries are possible

A "Generate Test Query" button would eliminate this friction by automatically creating interesting, relevant queries based on the actual database schema.

## Solution Statement
Implement a new "Generate Test Query" button that:
1. Appears in the UI between the "Query" and "Upload Data" buttons
2. Is styled with bright red background and includes a loading animation during processing
3. Calls the LLM (using existing `llm_processor.py` infrastructure) to generate interesting natural language queries based on available tables and schema
4. Automatically populates the query input field with the generated query (overwriting any existing content)
5. Allows users to click the button multiple times to generate different queries
6. Keeps queries concise (maximum two sentences)
7. Generates queries that stay within the bounds of expected database functionality

## Relevant Files
Use these files to implement the feature:

### Backend Files
- **`app/server/core/llm_processor.py`** - Contains the existing LLM integration logic for OpenAI and Anthropic. We'll add a new function `generate_test_query()` to create natural language queries based on database schema.

- **`app/server/core/sql_processor.py`** - Contains `get_database_schema()` function that retrieves current database structure. This will be used to provide schema context to the LLM for query generation.

- **`app/server/core/data_models.py`** - Contains Pydantic models for API requests/responses. We'll add a `GenerateTestQueryRequest` and `GenerateTestQueryResponse` model.

- **`app/server/server.py`** - Main FastAPI server file. We'll add a new endpoint `POST /api/generate-test-query` that calls the LLM to generate queries.

- **`app/server/tests/core/test_llm_processor.py`** - Test file for LLM processor. We'll add tests for the new `generate_test_query()` function.

### Frontend Files
- **`app/client/src/main.ts`** - Main TypeScript file containing UI logic. We'll add:
  - Event handler for the new "Generate Test Query" button
  - Function to call the new API endpoint
  - Logic to populate the query input field with generated queries

- **`app/client/src/types.d.ts`** - TypeScript type definitions. We'll add types for `GenerateTestQueryRequest` and `GenerateTestQueryResponse`.

- **`app/client/src/api/client.ts`** - API client module. We'll add a new function to call the `/api/generate-test-query` endpoint.

- **`app/client/src/style.css`** - Stylesheet. We'll add styles for the red button and loading animation.

- **`app/client/index.html`** - HTML structure. We'll add the new button element between the existing Query and Upload Data buttons.

### Testing Files
- **`app/server/tests/test_generate_query.py`** (New) - Unit tests for the generate test query functionality

### New Files
- **`.claude/commands/e2e/test_generate_query.md`** - E2E test file to validate the Generate Test Query button functionality

## Implementation Plan

### Phase 1: Foundation
1. Add Pydantic models for the new API request/response
2. Implement backend LLM function to generate test queries based on schema
3. Create FastAPI endpoint to expose this functionality
4. Add comprehensive unit tests for the new backend logic

### Phase 2: Core Implementation
1. Update frontend TypeScript types to match backend models
2. Implement API client function to call the new endpoint
3. Add the "Generate Test Query" button to the HTML structure
4. Create CSS styles for the red button with loading animation
5. Wire up event handlers and populate query input field with generated queries

### Phase 3: Integration
1. Test the complete flow from button click to query population
2. Ensure the feature works with multiple clicks (generating different queries each time)
3. Verify error handling when no tables are available
4. Create E2E test to validate the feature end-to-end
5. Run all validation commands to ensure zero regressions

## Step by Step Tasks

### Task 1: Add Backend Data Models
- Open `app/server/core/data_models.py`
- Add `GenerateTestQueryRequest` model (empty or with optional parameters)
- Add `GenerateTestQueryResponse` model with `query: str` and optional `error: str` fields

### Task 2: Implement LLM Test Query Generation Function
- Open `app/server/core/llm_processor.py`
- Create new function `generate_test_query(schema_info: Dict[str, Any], provider: str) -> str`
- Function should use existing OpenAI/Anthropic infrastructure
- Create a prompt that asks the LLM to generate an interesting natural language query based on the schema
- Limit response to 2 sentences maximum
- Ensure queries stay within expected database functionality (SELECT queries only)
- Handle both OpenAI and Anthropic providers with appropriate routing

### Task 3: Create FastAPI Endpoint
- Open `app/server/server.py`
- Add new endpoint `POST /api/generate-test-query` with response model `GenerateTestQueryResponse`
- Endpoint should:
  - Get current database schema using `get_database_schema()`
  - Call `generate_test_query()` from `llm_processor.py`
  - Return the generated query or error message
  - Log success/failure appropriately

### Task 4: Add Backend Unit Tests
- Create `app/server/tests/test_generate_query.py`
- Test `generate_test_query()` function with sample schema
- Test error handling when no tables exist
- Test that generated queries are reasonable and within bounds
- Mock LLM calls to avoid API costs during testing

### Task 5: Update Frontend Type Definitions
- Open `app/client/src/types.d.ts`
- Add `GenerateTestQueryRequest` interface
- Add `GenerateTestQueryResponse` interface matching backend Pydantic models

### Task 6: Add Frontend API Client Function
- Open `app/client/src/api/client.ts`
- Add `generateTestQuery()` function that calls `POST /api/generate-test-query`
- Handle response and errors appropriately

### Task 7: Add Generate Test Query Button to HTML
- Open `app/client/index.html`
- Add new button with id `generate-test-query-button` in the query-controls div
- Position it between the `query-button` and `upload-data-button`
- Add appropriate class for styling

### Task 8: Style the Generate Test Query Button
- Open `app/client/src/style.css`
- Add styles for `.generate-test-query-button` class:
  - Bright red background color
  - White text
  - Appropriate padding and border radius
  - Hover effect
- Add keyframe animation for loading state (e.g., pulsing or rotating effect)
- Add `.generate-test-query-button.loading` class with animation

### Task 9: Implement Button Click Handler
- Open `app/client/src/main.ts`
- Add `initializeGenerateTestQuery()` function
- Implement click handler that:
  - Disables button and shows loading animation
  - Calls `api.generateTestQuery()`
  - Populates query input field with generated query (overwrites existing content)
  - Re-enables button after completion
  - Handles errors gracefully with user-visible error messages
- Call `initializeGenerateTestQuery()` from `DOMContentLoaded` event listener

### Task 10: Create E2E Test File
- Read `.claude/commands/test_e2e.md` and `.claude/commands/e2e/test_basic_query.md` for examples
- Create `.claude/commands/e2e/test_generate_query.md`
- E2E test should validate:
  - Button appears between Query and Upload Data buttons
  - Button has red styling
  - Clicking button shows loading animation
  - Query input field is populated with generated query
  - User can click button multiple times and get different queries
  - Generated query can be executed via the Query button
- Include at least 4 screenshots: initial state, button click with loading, populated query, query results

### Task 11: Run Validation Commands
- Execute all validation commands listed in the "Validation Commands" section
- Ensure zero regressions in backend tests, frontend type checking, and frontend build
- Execute the new E2E test to validate end-to-end functionality
- Fix any issues that arise

## Testing Strategy

### Unit Tests
1. **LLM Function Tests** (`test_generate_query.py`):
   - Test `generate_test_query()` with various schema configurations
   - Test with empty schema (no tables)
   - Test with single table schema
   - Test with multiple table schema
   - Verify generated queries are reasonable and within bounds
   - Mock LLM API calls to avoid costs

2. **API Endpoint Tests** (add to existing test suite):
   - Test `POST /api/generate-test-query` returns valid response
   - Test error handling when database is empty
   - Test both OpenAI and Anthropic provider routing

### Integration Tests
1. Test complete flow: button click → API call → query population
2. Test multiple consecutive button clicks generate different queries
3. Test that generated queries can be successfully executed
4. Test error handling when LLM is unavailable

### E2E Tests
1. Validate button appears in correct position
2. Validate styling (red button, loading animation)
3. Validate query input field is populated
4. Validate generated query executes successfully
5. Capture screenshots for visual verification

### Edge Cases
1. **No tables loaded**: Should display helpful error message
2. **LLM API failure**: Should gracefully handle and show user-friendly error
3. **Empty query response**: Should handle and regenerate or show error
4. **Very long generated query**: Should truncate or reject queries longer than 2 sentences
5. **User has text in query box**: Should warn or simply overwrite (as specified in requirements)
6. **Button clicked rapidly multiple times**: Should prevent multiple simultaneous API calls
7. **Database with complex schema**: Should generate appropriate query for complex structures

## Acceptance Criteria
1. ✅ A "Generate Test Query" button appears between the "Query" and "Upload Data" buttons
2. ✅ The button has a bright red background with white text
3. ✅ A loading animation displays on the button while the LLM processes the request
4. ✅ Clicking the button generates a natural language query based on available tables and schema
5. ✅ The generated query automatically populates the query input field, overwriting any existing content
6. ✅ Generated queries are concise (maximum 2 sentences)
7. ✅ Generated queries stay within expected database functionality (no destructive operations)
8. ✅ Users can click the button multiple times to generate different queries
9. ✅ The generated query can be immediately executed via the existing "Query" button
10. ✅ If no tables exist, a helpful error message is displayed
11. ✅ All existing tests pass (zero regressions)
12. ✅ New E2E test validates the complete feature functionality
13. ✅ Frontend builds without TypeScript errors
14. ✅ Backend tests pass without errors

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

1. `cd app/server && uv run pytest tests/test_generate_query.py -v` - Run new unit tests for generate query feature
2. `cd app/server && uv run pytest` - Run all server tests to validate zero regressions
3. `cd app/client && bun tsc --noEmit` - Run frontend type checking to validate zero regressions
4. `cd app/client && bun run build` - Run frontend build to validate it works with zero regressions
5. Read `.claude/commands/test_e2e.md`, then read and execute `.claude/commands/e2e/test_generate_query.md` to validate the Generate Test Query button functionality end-to-end

## Notes

### LLM Prompt Design
The prompt for generating test queries should:
- Include full database schema (table names, column names, types, row counts)
- Instruct the LLM to generate interesting, realistic queries
- Limit complexity to queries that showcase the system's capabilities
- Emphasize SELECT queries only (no INSERT, UPDATE, DELETE, DROP)
- Request queries that would produce interesting results
- Specify maximum 2 sentences in natural language

### Example LLM Prompt Structure
```
Given the following database schema:

Table: users
Columns:
  - id (INTEGER)
  - name (TEXT)
  - email (TEXT)
  - signup_date (TEXT)
Row count: 20

Table: products
Columns:
  - id (INTEGER)
  - name (TEXT)
  - price (REAL)
  - category (TEXT)
Row count: 32

Generate a natural language query that would be interesting to run against this database. The query should showcase the system's ability to convert natural language to SQL. Keep it to 2 sentences maximum. Only suggest queries that retrieve data (SELECT operations).

Example: "Show me all users who signed up in the last month and their email addresses."

Your query:
```

### UI/UX Considerations
- **Button placement**: Between Query and Upload Data buttons for easy discovery
- **Color choice**: Bright red makes it visually distinct and attention-grabbing (indicates "test/experimental" functionality)
- **Loading animation**: Provides feedback during the 1-3 second LLM call
- **Overwrite behavior**: Always overwrite existing query text to avoid confusion about what will be executed
- **Error messaging**: If no tables exist, show: "Please upload data first to generate test queries"
- **Button state**: Disable during loading to prevent multiple simultaneous calls

### Future Enhancements (Out of Scope)
- Add ability to generate queries for specific tables only
- Add "history" of generated queries
- Allow users to rate generated queries for quality feedback
- Support for generating multiple queries at once
- Advanced query types (aggregations, joins, subqueries) with difficulty levels

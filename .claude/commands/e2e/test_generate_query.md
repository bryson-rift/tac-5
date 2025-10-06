# E2E Test: Generate Test Query Button

Test the Generate Test Query button functionality in the Natural Language SQL Interface application.

## User Story

As a user of the Natural Language SQL Interface
I want a button that automatically generates example queries for my database
So that I can quickly test the system's capabilities and explore my data without having to think of queries myself

## Test Steps

1. Navigate to the `Application URL`
2. Take a screenshot of the initial state
3. **Verify** the page title is "Natural Language SQL Interface"
4. **Verify** core UI elements are present:
   - Query input textbox
   - Query button
   - Generate Test Query button (red button between Query and Upload Data buttons)
   - Upload Data button
   - Available Tables section

5. **Verify** the Generate Test Query button has the correct styling:
   - Bright red background color
   - White text
   - Located between Query and Upload Data buttons

6. Click the "Upload Data" button to open the upload modal
7. Take a screenshot of the upload modal
8. Click on the "Users Data" sample button to load sample data
9. Wait for the data to load and the modal to close
10. **Verify** the "users" table appears in the Available Tables section

11. Click the "Generate Test Query" button
12. **Verify** the button shows loading state (pulsing animation and "Generating..." text)
13. Take a screenshot of the button in loading state
14. Wait for the test query to be generated
15. **Verify** the query input field is populated with a generated query
16. **Verify** the generated query is natural language (not SQL)
17. **Verify** the generated query is concise (maximum 2 sentences)
18. Take a screenshot of the populated query input

19. Click the "Generate Test Query" button again
20. Wait for a new query to be generated
21. **Verify** a different query is generated (shows variety)
22. Take a screenshot of the second generated query

23. Click the "Query" button to execute the generated query
24. Wait for results to appear
25. **Verify** the results display successfully
26. **Verify** the SQL translation is shown
27. Take a screenshot of the query results

28. Clear all tables by removing the users table
29. Click the "Generate Test Query" button with no tables loaded
30. **Verify** an error message is displayed: "Please upload data first to generate test queries"
31. Take a screenshot of the error message

## Success Criteria

- Generate Test Query button appears in correct position (between Query and Upload Data buttons)
- Generate Test Query button has bright red background with white text
- Clicking button shows loading animation (pulsing effect)
- Clicking button displays "Generating..." text during processing
- Query input field is populated with generated natural language query
- Generated query is concise (2 sentences or less)
- Generated query is in natural language (not SQL)
- Multiple clicks generate different queries (variety)
- Generated queries can be successfully executed via the Query button
- When no tables exist, helpful error message is displayed
- At least 6 screenshots are taken

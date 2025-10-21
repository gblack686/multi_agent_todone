# E2E Test: Data Generation Feature

Test synthetic data generation functionality in the Natural Language SQL Interface application.

## User Story

As a user  
I want to generate synthetic data based on existing table patterns  
So that I can expand my test datasets with realistic data

## Test Steps

1. Navigate to the `Application URL`
2. Take a screenshot of the initial state
3. **Verify** the page title is "Natural Language SQL Interface"
4. **Verify** Available Tables section is present

5. Upload sample data:
   - Click "Upload Data" button
   - Click the "Users" sample data button
   - **Verify** success message appears showing table was created
   - Take a screenshot of the success message

6. **Verify** the "users" table appears in Available Tables section
7. **Verify** the Generate Data button (✨ Generate) is visible to the left of the CSV export button
8. Take a screenshot of the table with Generate Data button

9. Note the current row count displayed for the users table
10. Click the Generate Data button
11. **Verify** the button shows a loading spinner
12. Take a screenshot of the loading state

13. Wait for the generation to complete (up to 30 seconds)
14. **Verify** a success message appears (e.g., "Successfully generated and inserted 10 rows")
15. Take a screenshot of the success message

16. **Verify** the row count for the users table has increased by 10
17. Take a screenshot of the updated table information

18. Query the generated data:
    - Enter query: "Show me the last 10 rows from users order by rowid desc"
    - Click Query button
    - **Verify** query results appear
    - **Verify** 10 rows are returned
    - Take a screenshot of the generated data

## Success Criteria
- Generate Data button appears for each table
- Button shows loading state during generation
- Success message displays after generation
- Row count increases by 10
- Generated data follows existing patterns
- Generated data can be queried successfully
- 6 screenshots are taken

## Error Scenarios
- If table is empty, should show appropriate error
- If LLM fails, should show error message
- Button should be re-enabled after error
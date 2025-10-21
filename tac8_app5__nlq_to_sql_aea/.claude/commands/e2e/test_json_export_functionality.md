# E2E Test: JSON Export Functionality

Test table and query result JSON export functionality in the Natural Language SQL Interface application.

## User Story

As a data analyst or developer  
I want to export table data and query results as JSON files  
So that I can easily integrate the data with modern applications, APIs, or data processing pipelines that prefer JSON format over CSV

## Test Steps

1. Navigate to the `Application URL`
2. Take a screenshot of the initial state
3. **Verify** the page title is "Natural Language SQL Interface"
4. **Verify** core UI elements are present:
   - Query input textbox
   - Query button
   - Upload Data button
   - Available Tables section

5. Upload a test CSV file containing sample data with various data types
6. **Verify** the table appears in the Available Tables section
7. **Verify** two export buttons appear to the left of the 'x' icon for the table:
   - A download icon button (for CSV export)
   - A "JSON" text button (for JSON export)
8. Take a screenshot of the table with both export buttons

9. Click the "JSON" button for the table
10. **Verify** a JSON file is downloaded with the name "{table_name}_export.json"
11. **Verify** the downloaded file contains valid JSON with:
    - An array of objects
    - Each object representing a row
    - Proper data types preserved (numbers as numbers, strings as strings)
    - Null values properly represented
    - Pretty-printed format with indentation

12. Enter a query: "SELECT * FROM uploaded_table LIMIT 5"
13. Click the Query button
14. **Verify** the query results appear
15. **Verify** two export buttons appear to the left of the 'Hide' button:
    - A download icon button (for CSV export)
    - A "JSON" text button (for JSON export)
16. Take a screenshot of query results with both export buttons

17. Click the "JSON" button for query results
18. **Verify** a JSON file is downloaded named "query_results.json"
19. **Verify** the downloaded file contains:
    - Valid JSON array
    - Correct number of rows (5)
    - All columns from the query
    - Proper data types preserved

20. Execute a query with special characters: "SELECT 'Test, "quoted"' as col1, 'Line\nbreak' as col2"
21. Click the "JSON" button for the results
22. **Verify** the JSON file properly escapes special characters

23. Execute an empty result query: "SELECT * FROM uploaded_table WHERE 1=0"
24. **Verify** the "JSON" button is still present
25. Click the "JSON" button
26. **Verify** an empty JSON array "[]" is downloaded

27. Upload a table with Unicode characters (e.g., emojis, international characters)
28. Export the table as JSON
29. **Verify** Unicode characters are preserved correctly in the JSON file

30. Take a screenshot of the final state

## Success Criteria
- JSON export buttons appear in correct positions (alongside CSV buttons)
- JSON buttons are visually distinct from CSV buttons (text "JSON" vs icon)
- Table JSON export downloads complete table as valid JSON
- Query JSON export downloads current results as valid JSON
- JSON files have appropriate names ({table_name}_export.json, query_results.json)
- JSON format is properly structured and pretty-printed
- Data types are preserved (numbers, strings, booleans, nulls)
- Special characters and Unicode are handled correctly
- Empty results produce valid empty JSON array "[]"
- All download operations complete successfully
- Both CSV and JSON export options remain functional
- 4 screenshots are taken
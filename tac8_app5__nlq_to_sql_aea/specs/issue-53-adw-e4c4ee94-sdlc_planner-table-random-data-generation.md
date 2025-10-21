# Feature: Table Random Data Generation Based on Schema Using LLMs

## Metadata
issue_number: `53`
adw_id: `e4c4ee94`
issue_json: `{"number":53,"title":"Table Random Data Generation Based on Schema Using LLMs","body":"Generate synthetic data rows based on existing table patterns and schema\n\n/feature\n\nadw_sdlc_iso\n\nmodel_set heavy\n\nImplement a random data generation feature that creates synthetic data rows based on existing table patterns. Add a new button to the left of the CSV export button in the Available Tables section that triggers LLM-based data generation.\n\nImplementation details:\n- Add \"Generate Data\" button with appropriate icon next to each table (left of CSV export)\n- When clicked, sample 10 random existing rows from the table\n- Send sampled data + table schema to LLM with prompt to understand data patterns\n- Generate 10 new synthetic rows that match the patterns and constraints\n- Insert generated rows into the table with proper validation\n- Show success notification with count of rows added\n\nThe LLM should analyze:\n- Data types and formats for each column\n- Value ranges and distributions\n- Relationships between columns\n- Common patterns (emails, phone numbers, addresses, etc.)\n- Nullable vs required fields\n\nUpdate the UI to show a loading state during generation and handle errors gracefully. The feature should use the existing LLM processor module and respect SQL security constraints.\n\nThis enhances testing and development by allowing users to quickly expand their datasets with realistic synthetic data."}`

## Feature Description
This feature adds the ability to generate synthetic data rows for existing tables using LLM analysis of table patterns and schema. Users can click a "Generate Data" button next to each table in the Available Tables section, which will sample existing data, analyze patterns using LLM, and generate 10 new realistic synthetic rows that match the table's structure and data patterns. The generated rows are inserted into the table with proper validation, enhancing testing and development workflows.

## User Story
As a developer or data analyst
I want to generate synthetic data that matches my existing table patterns
So that I can expand my test datasets with realistic data for development and testing

## Problem Statement
Developers and data analysts often need larger datasets for testing and development purposes. Manually creating test data is time-consuming and often results in unrealistic data that doesn't match existing patterns. Current solutions require external tools or manual scripting to generate synthetic data that matches specific schemas and patterns.

## Solution Statement
Implement an LLM-powered data generation feature that analyzes existing table data and schema to understand patterns, then generates synthetic rows that realistically match those patterns. The solution integrates seamlessly into the existing UI with a "Generate Data" button next to each table, making it easy to expand datasets with realistic synthetic data while respecting SQL security constraints.

## Relevant Files
Use these files to implement the feature:

- `README.md` - Project overview and structure understanding
- `app/client/src/main.ts` - Frontend main application logic where table UI is rendered and button functionality is implemented
- `app/client/src/api/client.ts` - API client for making requests to the backend, needs new endpoint for data generation
- `app/client/src/style.css` - Styling for the new Generate Data button
- `app/client/index.html` - HTML structure where UI elements are defined
- `app/server/server.py` - Backend server where new API endpoint will be added
- `app/server/core/llm_processor.py` - Existing LLM processor module to extend with data generation functionality
- `app/server/core/file_processor.py` - Contains database insertion logic and patterns
- `app/server/core/sql_security.py` - SQL security constraints to respect when inserting generated data
- `app/server/core/data_models.py` - Data models for request/response structures
- `app/server/core/sql_processor.py` - SQL execution logic
- `.claude/commands/test_e2e.md` - E2E test framework documentation
- `.claude/commands/e2e/test_basic_query.md` - Example E2E test for reference

### New Files
- `app/server/core/data_generator.py` - New module for LLM-based data generation logic
- `.claude/commands/e2e/test_data_generation.md` - E2E test for the data generation feature

## Implementation Plan
### Phase 1: Foundation
Create the backend infrastructure for data generation including the new data generator module, API endpoint, and data models. This phase establishes the core functionality for sampling existing data, analyzing patterns with LLM, and generating synthetic rows.

### Phase 2: Core Implementation
Implement the frontend UI components including the Generate Data button, loading states, and success notifications. Integrate the frontend with the backend API and ensure proper error handling throughout the data generation flow.

### Phase 3: Integration
Integrate the feature with existing SQL security constraints, ensure proper validation of generated data, and implement comprehensive error handling. Add logging and monitoring for the data generation process.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Create Data Generator Module
- Create `app/server/core/data_generator.py` with LLM-based data generation logic
- Implement function to sample random rows from a table
- Implement function to analyze data patterns using LLM
- Implement function to generate synthetic rows based on patterns
- Add proper error handling and logging

### 2. Extend LLM Processor
- Add new functions in `app/server/core/llm_processor.py` for data generation prompts
- Create prompts that analyze data patterns and generate synthetic data
- Ensure support for both OpenAI and Anthropic providers
- Add proper error handling for LLM failures

### 3. Create Data Models
- Add new request/response models in `app/server/core/data_models.py`
- Create `DataGenerationRequest` model with table_name field
- Create `DataGenerationResponse` model with generated rows and count
- Add validation for request parameters

### 4. Implement Backend API Endpoint
- Add new POST endpoint `/api/generate-data` in `app/server/server.py`
- Implement logic to handle data generation requests
- Use SQL security module to validate table names and operations
- Implement database insertion with proper validation
- Add comprehensive error handling and logging

### 5. Create E2E Test Specification
- Create `.claude/commands/e2e/test_data_generation.md` based on existing examples
- Define test steps to validate data generation functionality
- Include steps to verify UI elements, loading states, and success notifications
- Add validation for generated data insertion

### 6. Update Frontend API Client
- Add new method `generateTableData` in `app/client/src/api/client.ts`
- Implement proper error handling for the API call
- Add TypeScript types for request/response

### 7. Implement Frontend UI Components
- Add Generate Data button in `app/client/src/main.ts` next to each table (left of CSV export)
- Implement click handler for the Generate Data button
- Add loading state during data generation
- Implement success notification showing count of rows added
- Add error handling and display

### 8. Style the Generate Data Button
- Add CSS styles in `app/client/src/style.css` for the Generate Data button
- Ensure consistent styling with existing buttons
- Add hover and active states
- Style loading spinner for button

### 9. Implement Data Validation
- Add validation in data generator to ensure generated data matches schema types
- Validate nullable vs required fields
- Ensure generated data respects column constraints
- Add proper error messages for validation failures

### 10. Add Unit Tests
- Create unit tests for data generator module
- Test LLM prompt generation and parsing
- Test data validation logic
- Test error handling scenarios

### 11. Integration Testing
- Test the complete flow from UI button click to data insertion
- Verify loading states and notifications work correctly
- Test error scenarios (invalid table, LLM failure, etc.)
- Ensure SQL security is maintained

### 12. Run Validation Commands
Execute all validation commands to ensure the feature works correctly with zero regressions.

## Testing Strategy
### Unit Tests
- Test data sampling logic with various table structures
- Test LLM prompt generation for different data patterns
- Test synthetic data generation matching schema constraints
- Test data validation before insertion
- Test error handling for edge cases

### Edge Cases
- Empty tables (no existing data to sample)
- Tables with only one row
- Tables with complex data types (JSON, nested structures)
- Tables with foreign key constraints
- Large tables with millions of rows
- Network failures during LLM calls
- Invalid or malformed LLM responses
- SQL injection attempts through generated data
- Tables with special characters in names
- Concurrent data generation requests

## Acceptance Criteria
- Generate Data button appears to the left of CSV export button for each table
- Clicking the button shows a loading state on the button
- System samples 10 random rows from the existing table
- LLM analyzes patterns and generates 10 new synthetic rows
- Generated data matches table schema and data types
- Generated data follows patterns found in existing data
- Generated rows are successfully inserted into the table
- Success notification shows count of rows added
- Error messages are clear and actionable
- Feature respects all SQL security constraints
- No regression in existing functionality

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- Read `.claude/commands/test_e2e.md`, then read and execute your new E2E `.claude/commands/e2e/test_data_generation.md` test file to validate this functionality works
- `cd app/server && uv run pytest tests/core/test_data_generator.py -v` - Run data generator unit tests
- `cd app/server && uv run pytest` - Run server tests to validate the feature works with zero regressions
- `cd app/client && bun tsc --noEmit` - Run frontend tests to validate the feature works with zero regressions
- `cd app/client && bun run build` - Run frontend build to validate the feature works with zero regressions
- Manual test: Upload a CSV file, click Generate Data, verify 10 new rows are added
- Manual test: Try Generate Data on multiple tables to ensure it works consistently
- Manual test: Verify error handling by attempting to generate data for a non-existent table

## Notes
- Consider adding configuration options in the future for number of rows to generate
- Future enhancement could allow users to specify custom constraints or patterns
- Monitor LLM token usage as analyzing large datasets could be expensive
- Consider caching analyzed patterns for frequently used tables
- The feature uses `uv add` if new Python dependencies are needed for data generation
- Ensure generated data doesn't violate any unique constraints in the database
- Consider implementing rate limiting for data generation to prevent abuse
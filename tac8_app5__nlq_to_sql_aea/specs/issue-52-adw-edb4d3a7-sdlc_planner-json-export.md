# Feature: Add JSON Export

## Metadata
issue_number: `52`
adw_id: `edb4d3a7`
issue_json: `{"number":52,"title":"Add json export","body":"feature - adw_sdlc_iso - update to support table and query result 'json' export. Similar to our csv export but specifically built for json export."}`

## Feature Description
This feature extends the existing CSV export functionality to support JSON format exports for both database tables and query results. Users will be able to export their data in JSON format, which is widely used for data interchange, API integration, and modern data processing workflows. The JSON export will maintain the same user experience as the existing CSV export but output structured JSON data instead.

## User Story
As a data analyst or developer
I want to export table data and query results as JSON files
So that I can easily integrate the data with modern applications, APIs, or data processing pipelines that prefer JSON format over CSV

## Problem Statement
The current application only supports CSV export functionality. While CSV is useful for spreadsheet applications, many modern data workflows and integrations require JSON format for:
- API data interchange
- NoSQL database imports
- JavaScript application consumption
- Data pipeline processing
- Modern analytics tools

## Solution Statement
Extend the existing export infrastructure to support JSON format by:
- Creating JSON export utilities similar to the existing CSV export functions
- Adding new API endpoints for JSON export operations
- Implementing client-side JSON download functionality
- Adding JSON export buttons to the UI alongside existing CSV export buttons
- Following the same security patterns and validation as CSV exports

## Relevant Files
Use these files to implement the feature:

- `app/server/core/export_utils.py` - Contains existing CSV export functions that will be extended with JSON equivalents
- `app/server/core/data_models.py` - Contains ExportRequest and QueryExportRequest models that may need JSON-specific variants
- `app/server/server.py` - Contains CSV export endpoints that will be mirrored for JSON export
- `app/client/src/api/client.ts` - Contains CSV export API methods that will be extended for JSON
- `app/client/src/main.ts` - Contains UI components with CSV export buttons that will get JSON export buttons
- `app/client/src/style.css` - Contains styling for export buttons that may need updates for JSON buttons
- `app/server/tests/test_export_utils.py` - Contains CSV export tests that will be extended for JSON
- `app_docs/feature-490eb6b5-one-click-table-exports.md` - Documentation for CSV export functionality to understand patterns
- `.claude/commands/test_e2e.md` - E2E test runner documentation
- `.claude/commands/e2e/test_basic_query.md` - Example E2E test structure for understanding test patterns

### New Files
- `app/server/tests/test_json_export_utils.py` - Unit tests specifically for JSON export functionality
- `.claude/commands/e2e/test_json_export_functionality.md` - E2E test suite for JSON export features

## Implementation Plan
### Phase 1: Foundation
Create the core JSON export utilities and data models, ensuring they follow the same security and validation patterns as the existing CSV export infrastructure.

### Phase 2: Core Implementation
Implement the server-side JSON export endpoints and client-side API methods, maintaining consistency with the existing CSV export API design.

### Phase 3: Integration
Add JSON export buttons to the UI, integrate with existing components, and ensure the user experience is consistent with CSV export functionality.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Create JSON Export Utilities
- Add `generate_json_from_data()` function to `app/server/core/export_utils.py`
- Add `generate_json_from_table()` function to `app/server/core/export_utils.py`
- Ensure proper handling of SQLite data types, null values, and special characters
- Follow the same patterns as CSV functions but output JSON format
- Use Python's built-in `json` module for serialization

### 2. Create Unit Tests for JSON Export
- Create `app/server/tests/test_json_export_utils.py` with comprehensive test coverage
- Test empty data scenarios, various data types, Unicode characters, and special cases
- Mirror the test structure from `test_export_utils.py` but validate JSON output
- Test JSON schema validation and proper data type conversion

### 3. Add JSON Export API Endpoints
- Add `/api/export/table/json` endpoint to `app/server/server.py`
- Add `/api/export/query/json` endpoint to `app/server/server.py`
- Use existing security validation patterns from CSV endpoints
- Return JSON files with appropriate MIME type and Content-Disposition headers
- Implement proper error handling and logging

### 4. Update Data Models (if needed)
- Review if `ExportRequest` and `QueryExportRequest` models need JSON-specific variants
- Add any JSON-specific fields if required for format specification
- Ensure backward compatibility with existing CSV export functionality

### 5. Extend Client API Methods
- Add `exportTableAsJson()` method to `app/client/src/api/client.ts`
- Add `exportQueryResultsAsJson()` method to `app/client/src/api/client.ts`
- Follow the same patterns as CSV export methods but target JSON endpoints
- Handle JSON file downloads with appropriate filename extensions

### 6. Add JSON Export UI Components
- Add JSON export buttons to the Available Tables section in `app/client/src/main.ts`
- Add JSON export buttons to the Query Results section in `app/client/src/main.ts`
- Position JSON buttons consistently with existing CSV export buttons
- Use appropriate icons/text to distinguish JSON from CSV exports
- Update `app/client/src/style.css` with styling for JSON export buttons

### 7. Create E2E Test for JSON Export
- Create `.claude/commands/e2e/test_json_export_functionality.md`
- Test JSON export for both tables and query results
- Validate downloaded JSON files contain correct data structure
- Verify UI buttons work correctly and files download properly
- Include error scenarios and edge cases

### 8. Run Validation Commands
- Execute all validation commands to ensure zero regressions
- Verify both CSV and JSON export functionality work correctly
- Run comprehensive test suite to validate the feature

## Testing Strategy
### Unit Tests
- Test JSON generation from various data types (integers, floats, strings, booleans, null values)
- Test Unicode character handling in JSON export
- Test empty data scenarios and error conditions
- Test table export from SQLite database with JSON serialization
- Test query result export with proper JSON formatting
- Validate JSON schema correctness and data integrity

### Edge Cases
- Large datasets with 10,000+ rows to test performance
- Tables with special characters in column names
- Data containing JSON-like strings that need proper escaping
- Empty tables and empty query results
- Tables with mixed data types in columns
- Unicode and emoji characters in data
- Null values and empty strings in data

## Acceptance Criteria
- Users can export any database table as a JSON file
- Users can export query results as a JSON file
- JSON export buttons are clearly visible and positioned consistently with CSV buttons
- Downloaded JSON files contain properly formatted, valid JSON data
- JSON export maintains the same security validations as CSV export
- JSON files have appropriate filenames (e.g., `tablename_export.json`, `query_results.json`)
- Large datasets (up to 100,000 rows) export efficiently
- All existing CSV export functionality remains unaffected
- Comprehensive test coverage for all JSON export scenarios
- Zero regressions in existing application functionality

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `cd app/server && uv run pytest tests/test_json_export_utils.py -v` - Run JSON export unit tests
- `cd app/server && uv run pytest tests/test_export_utils.py -v` - Ensure CSV tests still pass
- Read `.claude/commands/test_e2e.md`, then read and execute `.claude/commands/e2e/test_json_export_functionality.md` - Run JSON export E2E tests
- Read `.claude/commands/test_e2e.md`, then read and execute `.claude/commands/e2e/test_export_functionality.md` - Ensure CSV export E2E tests still pass
- `cd app/server && uv run pytest` - Run server tests to validate the feature works with zero regressions
- `cd app/client && bun tsc --noEmit` - Run frontend tests to validate the feature works with zero regressions
- `cd app/client && bun run build` - Run frontend build to validate the feature works with zero regressions

## Notes
- JSON export leverages Python's built-in `json` module, avoiding new external dependencies
- JSON export buttons should use distinct icons or text to differentiate from CSV (e.g., "JSON" text or {} icon)
- JSON format preserves data types better than CSV (numbers remain numbers, booleans remain booleans)
- JSON export files should use proper MIME type `application/json` for download
- Future enhancements could include pretty-printed JSON with indentation options
- Consider JSON schema validation for exported data to ensure correctness
- Large datasets should be handled efficiently, potentially using streaming JSON generation for very large exports
- JSON export maintains the same security patterns as CSV, preventing SQL injection through table name validation
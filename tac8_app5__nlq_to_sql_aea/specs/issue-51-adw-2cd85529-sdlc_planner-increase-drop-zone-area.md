# Feature: Increase drop zone surface area

## Metadata
issue_number: `51`
adw_id: `2cd85529`
issue_json: `{"number":51,"title":"Increase drop zone surface area","body":"/feature\n\nadw_sdlc_iso\n\nlets increase the drop zone surface area. instead of having to click \"upload data\". The user can drag and drop right on to the upper div or lower div and the ui will update to a 'drop to create table' text. This runs the same usual functionality but enhances the ui to be more user friendly."}`

## Feature Description
This feature enhances the user experience by expanding the drag-and-drop functionality beyond the current upload modal. Users can now drag and drop files directly onto the main query section (upper div) or the tables section (lower div), eliminating the need to first click the "Upload Data" button. When files are dragged over these areas, the UI will provide visual feedback with "drop to create table" text, making the interface more intuitive and user-friendly.

## User Story
As a user
I want to drag and drop files directly onto the main interface areas
So that I can quickly upload data without having to open the upload modal first

## Problem Statement
Currently, users must click the "Upload Data" button to open a modal before they can drag and drop files. This adds an extra step to the upload process and makes the interface less intuitive, as the drag-and-drop zones are not immediately visible or accessible on the main interface.

## Solution Statement
Extend the drag-and-drop functionality to the main query section and tables section of the interface. When users drag files over these areas, provide visual feedback indicating they can drop to create a table. This maintains the existing upload functionality while making it more accessible and user-friendly.

## Relevant Files
Use these files to implement the feature:

- `app/client/src/main.ts:122-158` - Contains the existing file upload functionality that handles drag and drop events
- `app/client/index.html:14-47` - Contains the query section (upper div) and tables section (lower div) that need drag-drop support
- `app/client/src/style.css:247-263` - Contains existing drop-zone styling that can be extended for the new areas
- `app/client/src/api/client.ts` - Contains the uploadFile API call that will be reused
- `app/server/server.py` - Contains the upload endpoint that processes files (no changes needed)

### New Files
- `.claude/commands/e2e/test_enhanced_drop_zone.md` - E2E test to validate the enhanced drop zone functionality

## Implementation Plan
### Phase 1: Foundation
Analyze the existing drag-and-drop implementation in the upload modal and understand how to extend it to other DOM elements. Review the current file handling and upload process to ensure consistency.

### Phase 2: Core Implementation
Add drag-and-drop event listeners to the query section and tables section. Implement visual feedback (drop overlays) that appear when files are dragged over these areas. Ensure the same file validation and upload logic is applied.

### Phase 3: Integration
Test the enhanced functionality works seamlessly with the existing upload modal system. Ensure proper error handling and visual feedback throughout the process.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Create E2E test specification
- Read `.claude/commands/test_e2e.md` and `.claude/commands/e2e/test_basic_query.md` to understand E2E test format
- Create `.claude/commands/e2e/test_enhanced_drop_zone.md` that validates:
  - Files can be dragged over query section with visual feedback
  - Files can be dragged over tables section with visual feedback
  - Drop overlay shows "drop to create table" text
  - Files can be successfully dropped and uploaded from both areas
  - Existing upload modal functionality remains intact

### 2. Extend CSS for enhanced drop zones
- Add new CSS classes for drop overlays that will appear over the query and tables sections
- Style the drop overlays with "drop to create table" messaging
- Ensure visual consistency with existing drop-zone styling
- Add hover and dragover states for the new drop areas

### 3. Implement drag-and-drop for query section
- Add drag event listeners (dragover, dragleave, drop) to the query section
- Create and show drop overlay when files are dragged over the query section
- Handle file drop events and trigger the existing handleFileUpload function
- Ensure proper cleanup of event listeners and visual states

### 4. Implement drag-and-drop for tables section  
- Add drag event listeners (dragover, dragleave, drop) to the tables section
- Create and show drop overlay when files are dragged over the tables section
- Handle file drop events and trigger the existing handleFileUpload function
- Ensure proper cleanup of event listeners and visual states

### 5. Add visual feedback and animations
- Implement smooth transitions for drop overlay appearance/disappearance
- Add appropriate visual cues (borders, background changes) when dragging over drop areas
- Ensure the drop overlays don't interfere with existing UI elements

### 6. Test integration with existing functionality
- Verify that the original upload modal drag-and-drop still works
- Test file validation works correctly for all drop zones
- Ensure error handling is consistent across all upload methods
- Test with different file types (.csv, .json, .jsonl)

### 7. Run validation commands
- Execute all validation commands to ensure the feature works correctly with zero regressions

## Testing Strategy
### Unit Tests
No additional unit tests needed as this feature reuses existing upload logic and only adds new UI interactions.

### Edge Cases
- Dragging non-file items over the enhanced drop zones
- Dragging invalid file types over the new areas
- Multiple files dragged simultaneously
- Drag operations that start over one area and move to another
- Rapid drag enter/leave events that could cause visual glitches

## Acceptance Criteria
- Users can drag files over the query section and see visual feedback
- Users can drag files over the tables section and see visual feedback
- Drop overlays display "drop to create table" messaging
- Files dropped on either enhanced area successfully upload and create tables
- Original upload modal functionality remains unchanged
- Visual feedback is smooth and doesn't interfere with existing UI
- All file validation and error handling works consistently across all drop methods
- No regressions in existing upload functionality

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- Read `.claude/commands/test_e2e.md`, then read and execute the new E2E `.claude/commands/e2e/test_enhanced_drop_zone.md` test file to validate this functionality works
- `cd app/server && uv run pytest` - Run server tests to validate the feature works with zero regressions
- `cd app/client && bun tsc --noEmit` - Run frontend tests to validate the feature works with zero regressions
- `cd app/client && bun run build` - Run frontend build to validate the feature works with zero regressions

## Notes
- This feature enhances UX without changing core functionality
- Reuses existing upload logic to maintain consistency
- Visual feedback should be subtle but clear to avoid overwhelming the interface
- Consider accessibility implications for keyboard and screen reader users
- The implementation should be performant and not add unnecessary event listeners when not needed
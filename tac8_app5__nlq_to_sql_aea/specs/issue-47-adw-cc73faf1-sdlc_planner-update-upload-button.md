# Chore: Update Upload Button Text

## Metadata
issue_number: `47`
adw_id: `cc73faf1`
issue_json: `{"number":47,"title":"quick button change","body":"/chore adw_sdlc_ZTE_iso - update 'Upload Data' to be 'Upload'\n\n"}`

## Chore Description
Update the "Upload Data" button text to "Upload" in the client application. This is a simple UI text change to make the button more concise while maintaining its functionality.

## Relevant Files
Use these files to resolve the chore:

- `app/client/index.html` - Contains the HTML structure with the "Upload Data" button that needs to be updated to "Upload"
- `README.md` - Contains documentation that references the "Upload Data" button and may need to be updated for consistency

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Update Button Text in Client HTML
- Update the button text from "Upload Data" to "Upload" in `app/client/index.html` at line 25
- Ensure the button ID and CSS classes remain unchanged to maintain functionality

### Step 2: Update Documentation
- Update the README.md file to reflect the button text change from "Upload Data" to "Upload" in the usage section at line 78
- Ensure consistency between the actual UI and the documentation

### Step 3: Validation
- Run validation commands to ensure no regressions and that the application still works correctly

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `cd app/server && uv run pytest` - Run server tests to validate the chore is complete with zero regressions
- `cd app/client && bun run build` - Build the client to ensure no build errors after the text change

## Notes
- This is a simple text change that should not affect any functionality
- The modal header "Upload Data" in the modal should remain unchanged as it provides context for what the modal does
- Only the button text should be changed from "Upload Data" to "Upload" for a more concise UI
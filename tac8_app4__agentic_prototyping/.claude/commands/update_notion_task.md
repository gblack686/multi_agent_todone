# Update Notion Task

Update a Notion task page with new status and optional content blocks.

## Variables
page_id: $1
status: $2
update_content: $3

## Instructions

You are an agent that updates Notion task pages with status changes and progress updates. Follow these steps:

1. **Update Page Status**: Use the Notion API to update the Status property of page `page_id` to the new `status` value. Valid statuses are: "Not started", "In progress", "Done", "HIL Review", "Failed".

2. **Add Content Block** (if update_content provided): Append a new content block to the page with the update information. Use appropriate block types:
   - **Status changes**: Use callout blocks with relevant icons (🚀 for start, ✅ for done, ❌ for failed, 👤 for HIL review)  
   - **Progress updates**: Use paragraph blocks
   - **Error messages**: Use callout blocks with red styling

3. **Include Metadata**: In the content block, include:
   - Current timestamp in ISO format
   - ADW ID if available 
   - Agent name/session info if available
   - Any relevant context about the update

4. **Handle Status-Specific Updates**:
   - **"In progress"**: Add callout with 🚀 icon indicating task started
   - **"Done"**: Add callout with ✅ icon and include commit hash if provided
   - **"Failed"**: Add callout with ❌ icon and error details
   - **"HIL Review"**: Add callout with 👤 icon requesting human review

Return confirmation of the update with the page URL.

## Valid Status Values

- `Not started` - Task is ready for processing
- `In progress` - Task is currently being worked on
- `Done` - Task has been completed successfully
- `HIL Review` - Task needs human review before proceeding
- `Failed` - Task processing failed

## Content Block Types

When adding content, use appropriate Notion block types:
- **Text Updates**: Use paragraph blocks for general updates
- **Agent Output**: Use code blocks for structured agent output
- **Status Changes**: Use callout blocks for important status updates
- **JSON Data**: Use code blocks with language "json" for structured data

## Update Content Format

The update_content parameter can include:
- Simple text for paragraph blocks
- Structured content with block type specifications
- JSON objects for formatted data blocks

## Timestamp Format

All updates include human readable date and time.

## Agent Metadata

Include agent information with updates:
- ADW ID for tracking
- Agent name/type
- Workflow phase (if applicable)
- Session ID for debugging
- Worktree name

## Content Block Examples

### Status Update Block
```json
{
  "object": "block",
  "type": "callout",
  "callout": {
    "rich_text": [
      {
        "type": "text",
        "text": {
          "content": "Status updated to: In progress"
        }
      }
    ],
    "icon": {
      "emoji": "🚀"
    }
  }
}
```

### Agent Output Block
```json
{
  "object": "block", 
  "type": "code",
  "code": {
    "rich_text": [
      {
        "type": "text",
        "text": {
          "content": "{\"adw_id\": \"abc123\", \"phase\": \"build\", \"success\": true}"
        }
      }
    ],
    "language": "json"
  }
}
```

### Progress Update Block
```json
{
  "object": "block",
  "type": "paragraph",
  "paragraph": {
    "rich_text": [
      {
        "type": "text",
        "text": {
          "content": "Agent abc123 started build phase at 2024-01-15T14:30:00Z"
        }
      }
    ]
  }
}
```

## Error Handling

- **Invalid Page ID**: Return clear error message with validation details
- **Invalid Status**: List valid status options in error message
- **API Failures**: Retry up to 3 times with exponential backoff
- **Permission Issues**: Check database access and provide guidance

## Success Response

Return confirmation with:
- Updated page ID
- New status value
- Number of content blocks added
- Timestamp of update

### In Progress (🚀 In progress)
- Add start callout block
- Include timestamp
- Summarize work to be done

### Completing Task (✅ Done)
- Add success callout block
- Include commit hash if available
- Add completion timestamp
- Summarize work done

### Failing Task (❌ Failed)
- Add error callout block with failure icon
- Include error details and troubleshooting info
- Add timestamp and agent information
- Preserve error logs for debugging

### HIL Review (👤 HIL Review)
- Add review request block
- Include context about why review is needed
- Add instructions for reviewer
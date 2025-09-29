# Get Notion Tasks

Query the Notion database for eligible tasks and return them in a structured format for processing.

## Variables
database_id: $1
status_filter: $2
limit: $3

## Default Variable Values

- database_id: (REQUIRED) Must be provided. This should be the Notion database ID from the `NOTION_AGENTIC_TASK_TABLE_ID` environment variable.
- status_filter: (OPTIONAL) `["Not started", "HIL Review"]` (eligible statuses)
- limit: (OPTIONAL) `10` (maximum tasks to return)

## Instructions

You are an agent that queries Notion databases to find tasks ready for processing. Follow these steps:

1. **Query the Database**: Use the Notion API to query database `database_id` for tasks with status in `status_filter` (default: ["Not started", "HIL Review"]). Limit results to `limit` tasks (default: 10).

2. **For Each Task Retrieved**:
   - Get the full page content including all blocks
   - Check if the last content block starts with "execute" or "continue -" 
   - If not, skip this task (not ready for execution)
   - If yes, extract the task prompt and parse any `{{key: value}}` tags

3. **Extract Information**:
   - **Page ID**: The Notion page identifier
   - **Title**: From the Name property
   - **Status**: Current status value
   - **Tags**: Parse content for `{{worktree: name}}`, `{{model: opus}}`, `{{workflow: plan}}`, `{{app: appname}}`, `{{prototype: type}}` patterns
   - **Execution Trigger**: "execute" or "continue" based on last block
   - **Task Prompt**: Full content for "execute", or just the continue prompt for "continue -"

4. **Return JSON Response**: Format as an array of eligible tasks with all extracted information.


## Eligibility Criteria

A task is eligible for processing if:
1. Status is "Not started" or "HIL Review"
2. Last content block in the page starts with "execute" or "continue - <prompt>"
3. Task is not currently locked by another agent

## Tag Extraction

Extract tags from page content using the pattern `{{key: value}}`:
- `{{worktree: feature-auth}}` - Target worktree name
- `{{model: opus}}` - Claude model preference (opus/sonnet)
- `{{workflow: plan|build}}` - Force plan-implement workflow
- `{{app: sentiment_analysis}}` - Target app directory
- `{{prototype: uv_script|vite_vue|bun_scripts|uv_mcp}}` - Prototype type for app generation

## Execution Trigger Detection

Check the last content block for execution commands:
- `execute` - Process all page content as task prompt, combine into a single string for the task_prompt field
- `continue - <specific prompt>` - Process only the continue block content, combine into a single string for the task_prompt field

**CRITICAL**: Output MUST be valid JSON only. Do not include any text before or after the JSON array.

## Error Handling

- If database_id is invalid, return error message
- If no tasks are eligible, return empty array
- If Notion API fails, retry up to 3 times with exponential backoff
- Log all errors for debugging purposes

## Concurrent Access Control

- Check if task is already being processed (status "In progress")
- Skip tasks that have been modified in the last 30 seconds (potential race condition)
- Return tasks in order of creation (oldest first) for fairness

## Response Format

**IMPORTANT**: Return ONLY valid JSON. No markdown, no explanations, no summaries. Just the JSON array.

IMPORTANT: task_prompt should be all of the content blocks combined into a single string. This is critical for the agent to process the task.

Return JSON array with the following structure:

```json
[
  {
    "page_id": "notion-page-id",
    "title": "Task title from Name property",
    "status": "Not started",
    "content_blocks": [
      {
        "type": "paragraph",
        "paragraph": {
          "rich_text": [
            {
              "text": {
                "content": "Task description here"
              }
            }
          ]
        }
      }
    ],
    "tags": {
      "worktree": "feature-auth",
      "model": "opus",
      "workflow": "plan",
      "prototype": "vite_vue"
    },
    "execution_trigger": "execute",
    "task_prompt": "Extracted task description for agent processing"
  }
]
```
# Chore: Support better models for query generation

## Metadata
issue_number: `54`
adw_id: `0720754f`
issue_json: `{"number":54,"title":"Support better models for query generation","body":"chore - adw_sdlc_iso\n\nupdate openai model to use o4-mini (o4-mini-2025-04-16)"}`

## Chore Description
Update the OpenAI model configuration in the Natural Language SQL Interface application to use the newer o4-mini model (o4-mini-2025-04-16) for improved query generation performance. This chore involves updating the model string in the OpenAI API calls to leverage the latest o4-mini model for better accuracy and efficiency in natural language to SQL conversion.

## Relevant Files
Use these files to resolve the chore:

- `app/server/core/llm_processor.py:44` - Contains the OpenAI model configuration "gpt-4.1-2025-04-14" that needs to be updated to "o4-mini-2025-04-16" in the `generate_sql_with_openai` function
- `app/server/core/llm_processor.py:184` - Contains the OpenAI model configuration "gpt-4.1-2025-04-14" that needs to be updated to "o4-mini-2025-04-16" in the `generate_random_query_with_openai` function
- `app/server/tests/core/test_llm_processor.py` - Contains test cases that may reference the OpenAI model name and need to be updated to match the new model string

### New Files
No new files need to be created for this chore.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Update OpenAI model in SQL generation function
- Update the model parameter in `app/server/core/llm_processor.py:44` from "gpt-4.1-2025-04-14" to "o4-mini-2025-04-16" in the `generate_sql_with_openai` function

### Step 2: Update OpenAI model in random query generation function  
- Update the model parameter in `app/server/core/llm_processor.py:184` from "gpt-4.1-2025-04-14" to "o4-mini-2025-04-16" in the `generate_random_query_with_openai` function

### Step 3: Update corresponding test cases
- Review and update any test assertions in `app/server/tests/core/test_llm_processor.py` that reference the old model name to use the new "o4-mini-2025-04-16" model string

### Step 4: Run validation commands
- Execute the validation commands to ensure the chore is complete with zero regressions

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `cd app/server && uv run pytest` - Run server tests to validate the chore is complete with zero regressions
- `cd app/server && python -c "from core.llm_processor import generate_sql_with_openai, generate_random_query_with_openai; print('OpenAI model updated successfully')"` - Verify the updated functions can be imported without errors

## Notes
- This model update should maintain full backward compatibility with existing API interfaces
- The o4-mini model is expected to provide improved performance over the previous GPT-4.1 model
- No changes to environment variables or API key configuration are required
- The Anthropic model configuration remains unchanged and should continue using "claude-sonnet-4-0"
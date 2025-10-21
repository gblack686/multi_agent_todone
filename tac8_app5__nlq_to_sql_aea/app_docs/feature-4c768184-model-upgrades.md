# Model Upgrades for Better Query Generation

**ADW ID:** 4c768184
**Date:** July 29, 2025
**Specification:** specs/issue-9-adw-4c768184-sdlc_planner-support-better-models-query.md

## Overview

Updated the AI model configurations in the Natural Language SQL Interface application to use more advanced models for improved query generation accuracy and sophistication. The upgrade includes switching to Claude 4 Sonnet and GPT-4.1 latest models.

## What Was Built

- Upgraded Anthropic model integration from Claude 3 Haiku to Claude 4 Sonnet
- Upgraded OpenAI model integration from GPT-4.1 Mini to GPT-4.1 latest
- Updated corresponding test cases to reflect the new model configurations

## Technical Implementation

### Files Modified

- `app/server/core/llm_processor.py`: Updated model configurations for both OpenAI and Anthropic integrations across all functions
- `app/server/tests/core/test_llm_processor.py`: Updated test assertions to match new model names

### Key Changes

- OpenAI model upgraded from `gpt-4.1-mini` to `gpt-4.1-2025-04-14` in SQL generation and random query functions
- Anthropic model upgraded from `claude-3-haiku-20240307` to `claude-sonnet-4-0` in SQL generation and random query functions
- Test cases updated to verify correct model names are being used in API calls
- All function signatures and return types remain unchanged for backward compatibility

## How to Use

The model upgrades are transparent to end users. The Natural Language SQL Interface will automatically use the new models for:

1. Converting natural language queries to SQL (both OpenAI and Anthropic options)
2. Generating random/sample queries for exploration
3. All existing API endpoints continue to work without changes

## Configuration

No additional configuration is required. The system continues to use the same environment variables:
- `OPENAI_API_KEY` - for OpenAI API access
- `ANTHROPIC_API_KEY` - for Anthropic API access

## Testing

Run the validation commands to ensure the upgrade is working correctly:

```bash
cd app/server && uv run pytest
cd app/server && python -c "from core.llm_processor import generate_sql_with_openai, generate_sql_with_anthropic; print('Models updated successfully')"
```

## Notes

- The new models provide better performance and accuracy for SQL query generation
- All existing API interfaces remain unchanged
- The upgrade maintains full backward compatibility
- Users should expect improved quality in generated SQL queries and suggestions
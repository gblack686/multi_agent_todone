#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "anthropic",
#     "python-dotenv",
# ]
# ///

"""
AI-powered event summarizer for Claude Code hooks.
Generates concise summaries of hook events using Anthropic's Claude.
"""

import os
import json
from typing import Optional, Dict, Any

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv is optional

def generate_event_summary(event_data: Dict[str, Any]) -> Optional[str]:
    """
    Generate a concise summary of a hook event using Claude.
    
    Args:
        event_data: The event data dictionary containing hook information
        
    Returns:
        A string summary or None if generation fails
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    
    try:
        import anthropic
        
        # Extract key information from event
        hook_type = event_data.get('hook_event_type', 'Unknown')
        payload = event_data.get('payload', {})
        
        # Create a concise prompt
        if hook_type == 'PreToolUse':
            tool_name = payload.get('tool_name', 'Unknown')
            prompt = f"Summarize in 1 sentence: PreToolUse hook for {tool_name} tool"
        elif hook_type == 'PostToolUse':
            tool_name = payload.get('tool_name', 'Unknown')
            prompt = f"Summarize in 1 sentence: PostToolUse hook for {tool_name} tool"
        elif hook_type == 'UserPromptSubmit':
            user_prompt = payload.get('prompt', '')[:100]  # First 100 chars
            prompt = f"Summarize in 1 sentence: User submitted prompt: {user_prompt}"
        else:
            prompt = f"Summarize in 1 sentence: {hook_type} hook event occurred"
        
        # Generate summary
        client = anthropic.Anthropic(api_key=api_key)
        
        message = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=50,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}],
        )
        
        return message.content[0].text.strip()
        
    except Exception:
        return None


def main():
    """Test the summarizer with sample data."""
    sample_event = {
        'hook_event_type': 'PreToolUse',
        'payload': {
            'tool_name': 'Bash',
            'tool_input': {'command': 'ls -la'}
        }
    }
    
    summary = generate_event_summary(sample_event)
    if summary:
        print(f"Summary: {summary}")
    else:
        print("Failed to generate summary")


if __name__ == "__main__":
    main()
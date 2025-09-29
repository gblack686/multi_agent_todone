"""
Constants for JSONL file processing and field flattening.

This module defines the delimiter constants used for flattening nested JSON objects
and arrays into flat column names suitable for SQLite tables.

Delimiter System:
- NESTED_DELIMITER: Used to separate nested object keys (e.g., "user__profile__name")
- LIST_INDEX_DELIMITER: Used to separate list indices (e.g., "items_0", "items_1")

Examples:
- Nested object {"user": {"profile": {"name": "John"}}} becomes "user__profile__name"
- Array field {"items": ["a", "b"]} becomes "items_0" and "items_1"
- Complex structure {"tags": [{"name": "tag1"}, {"name": "tag2"}]} becomes "tags_0__name", "tags_1__name"
"""

# Delimiter for nested object fields
NESTED_DELIMITER = "__"

# Delimiter for list/array indices
LIST_INDEX_DELIMITER = "_"
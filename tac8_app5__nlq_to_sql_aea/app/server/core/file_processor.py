import json
import pandas as pd
import sqlite3
import io
import re
from typing import Dict, Any, Set
from .sql_security import (
    execute_query_safely,
    validate_identifier,
    SQLSecurityError
)
from .constants import NESTED_DELIMITER, LIST_INDEX_DELIMITER

def sanitize_table_name(table_name: str) -> str:
    """
    Sanitize table name for SQLite by removing/replacing bad characters
    and validating against SQL injection
    """
    # Remove file extension if present
    if '.' in table_name:
        table_name = table_name.rsplit('.', 1)[0]
    
    # Replace bad characters with underscores
    sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', table_name)
    
    # Ensure it starts with a letter or underscore
    if sanitized and not sanitized[0].isalpha() and sanitized[0] != '_':
        sanitized = '_' + sanitized
    
    # Ensure it's not empty
    if not sanitized:
        sanitized = 'table'
    
    # Validate the sanitized name
    try:
        validate_identifier(sanitized, "table")
    except SQLSecurityError:
        # If validation fails, use a safe default
        sanitized = f"table_{hash(table_name) % 100000}"
    
    return sanitized

def convert_csv_to_sqlite(csv_content: bytes, table_name: str, db_path: str = "db/database.db") -> Dict[str, Any]:
    """
    Convert CSV file content to SQLite table
    """
    try:
        # Sanitize table name
        table_name = sanitize_table_name(table_name)
        
        # Read CSV into pandas DataFrame
        df = pd.read_csv(io.BytesIO(csv_content))
        
        # Clean column names
        df.columns = [col.lower().replace(' ', '_').replace('-', '_') for col in df.columns]
        
        # Connect to SQLite database
        conn = sqlite3.connect(db_path)
        
        # Write DataFrame to SQLite
        df.to_sql(table_name, conn, if_exists='replace', index=False)
        
        # Get schema information using safe query execution
        cursor_info = execute_query_safely(
            conn,
            "PRAGMA table_info({table})",
            identifier_params={'table': table_name}
        )
        columns_info = cursor_info.fetchall()
        
        schema = {}
        for col in columns_info:
            schema[col[1]] = col[2]  # column_name: data_type
        
        # Get sample data using safe query execution
        cursor_sample = execute_query_safely(
            conn,
            "SELECT * FROM {table} LIMIT 5",
            identifier_params={'table': table_name}
        )
        sample_rows = cursor_sample.fetchall()
        column_names = [col[1] for col in columns_info]
        sample_data = [dict(zip(column_names, row)) for row in sample_rows]
        
        # Get row count using safe query execution
        cursor_count = execute_query_safely(
            conn,
            "SELECT COUNT(*) FROM {table}",
            identifier_params={'table': table_name}
        )
        row_count = cursor_count.fetchone()[0]
        
        conn.close()
        
        return {
            'table_name': table_name,
            'schema': schema,
            'row_count': row_count,
            'sample_data': sample_data
        }
        
    except Exception as e:
        raise Exception(f"Error converting CSV to SQLite: {str(e)}")

def convert_json_to_sqlite(json_content: bytes, table_name: str, db_path: str = "db/database.db") -> Dict[str, Any]:
    """
    Convert JSON file content to SQLite table
    """
    try:
        # Sanitize table name
        table_name = sanitize_table_name(table_name)
        
        # Parse JSON
        data = json.loads(json_content.decode('utf-8'))
        
        # Ensure it's a list of objects
        if not isinstance(data, list):
            raise ValueError("JSON must be an array of objects")
        
        if not data:
            raise ValueError("JSON array is empty")
        
        # Convert to pandas DataFrame
        df = pd.DataFrame(data)
        
        # Clean column names
        df.columns = [col.lower().replace(' ', '_').replace('-', '_') for col in df.columns]
        
        # Connect to SQLite database
        conn = sqlite3.connect(db_path)
        
        # Write DataFrame to SQLite
        df.to_sql(table_name, conn, if_exists='replace', index=False)
        
        # Get schema information using safe query execution
        cursor_info = execute_query_safely(
            conn,
            "PRAGMA table_info({table})",
            identifier_params={'table': table_name}
        )
        columns_info = cursor_info.fetchall()
        
        schema = {}
        for col in columns_info:
            schema[col[1]] = col[2]  # column_name: data_type
        
        # Get sample data using safe query execution
        cursor_sample = execute_query_safely(
            conn,
            "SELECT * FROM {table} LIMIT 5",
            identifier_params={'table': table_name}
        )
        sample_rows = cursor_sample.fetchall()
        column_names = [col[1] for col in columns_info]
        sample_data = [dict(zip(column_names, row)) for row in sample_rows]
        
        # Get row count using safe query execution
        cursor_count = execute_query_safely(
            conn,
            "SELECT COUNT(*) FROM {table}",
            identifier_params={'table': table_name}
        )
        row_count = cursor_count.fetchone()[0]
        
        conn.close()
        
        return {
            'table_name': table_name,
            'schema': schema,
            'row_count': row_count,
            'sample_data': sample_data
        }
        
    except Exception as e:
        raise Exception(f"Error converting JSON to SQLite: {str(e)}")

def flatten_json_object(obj: Any, prefix: str = "") -> Dict[str, Any]:
    """
    Flatten a nested JSON object using delimiter constants.
    
    Args:
        obj: The object to flatten (can be dict, list, or primitive)
        prefix: The current prefix for nested keys
        
    Returns:
        Dict with flattened key-value pairs
    """
    result = {}
    
    if isinstance(obj, dict):
        for key, value in obj.items():
            new_key = f"{prefix}{NESTED_DELIMITER}{key}" if prefix else key
            result.update(flatten_json_object(value, new_key))
    elif isinstance(obj, list):
        for i, value in enumerate(obj):
            new_key = f"{prefix}{LIST_INDEX_DELIMITER}{i}"
            result.update(flatten_json_object(value, new_key))
    else:
        # Primitive value (string, number, boolean, null)
        result[prefix] = obj
    
    return result

def discover_jsonl_fields(jsonl_content: bytes) -> Set[str]:
    """
    Discover all possible field names by scanning the entire JSONL file.
    
    Args:
        jsonl_content: The raw JSONL file content
        
    Returns:
        Set of all flattened field names found in the file
    """
    all_fields = set()
    
    try:
        content = jsonl_content.decode('utf-8')
        lines = content.strip().split('\n')
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
                
            try:
                json_obj = json.loads(line)
                flattened = flatten_json_object(json_obj)
                all_fields.update(flattened.keys())
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON on line {line_num}: {str(e)}")
    except UnicodeDecodeError:
        raise ValueError("File is not valid UTF-8 encoded text")
    
    return all_fields

def convert_jsonl_to_sqlite(jsonl_content: bytes, table_name: str, db_path: str = "db/database.db") -> Dict[str, Any]:
    """
    Convert JSONL file content to SQLite table with flattened structure.
    
    Args:
        jsonl_content: The raw JSONL file content
        table_name: Name for the SQLite table
        
    Returns:
        Dict containing table info, schema, row count, and sample data
    """
    try:
        # Sanitize table name
        table_name = sanitize_table_name(table_name)
        
        # First pass: discover all possible fields
        all_fields = discover_jsonl_fields(jsonl_content)
        
        if not all_fields:
            raise ValueError("No valid JSON objects found in JSONL file")
        
        # Second pass: process each line and create consistent records
        content = jsonl_content.decode('utf-8')
        lines = content.strip().split('\n')
        
        records = []
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
                
            try:
                json_obj = json.loads(line)
                flattened = flatten_json_object(json_obj)
                
                # Create record with all fields, filling missing ones with None
                record = {}
                for field in all_fields:
                    record[field] = flattened.get(field, None)
                
                records.append(record)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON on line {line_num}: {str(e)}")
        
        if not records:
            raise ValueError("No valid records found in JSONL file")
        
        # Convert to pandas DataFrame
        df = pd.DataFrame(records)
        
        # Clean column names for SQLite compatibility
        df.columns = [col.lower().replace(' ', '_').replace('-', '_') for col in df.columns]
        
        # Connect to SQLite database
        conn = sqlite3.connect(db_path)
        
        # Write DataFrame to SQLite
        df.to_sql(table_name, conn, if_exists='replace', index=False)
        
        # Get schema information using safe query execution
        cursor_info = execute_query_safely(
            conn,
            "PRAGMA table_info({table})",
            identifier_params={'table': table_name}
        )
        columns_info = cursor_info.fetchall()
        
        schema = {}
        for col in columns_info:
            schema[col[1]] = col[2]  # column_name: data_type
        
        # Get sample data using safe query execution
        cursor_sample = execute_query_safely(
            conn,
            "SELECT * FROM {table} LIMIT 5",
            identifier_params={'table': table_name}
        )
        sample_rows = cursor_sample.fetchall()
        column_names = [col[1] for col in columns_info]
        sample_data = [dict(zip(column_names, row)) for row in sample_rows]
        
        # Get row count using safe query execution
        cursor_count = execute_query_safely(
            conn,
            "SELECT COUNT(*) FROM {table}",
            identifier_params={'table': table_name}
        )
        row_count = cursor_count.fetchone()[0]
        
        conn.close()
        
        return {
            'table_name': table_name,
            'schema': schema,
            'row_count': row_count,
            'sample_data': sample_data
        }
        
    except Exception as e:
        raise Exception(f"Error converting JSONL to SQLite: {str(e)}")
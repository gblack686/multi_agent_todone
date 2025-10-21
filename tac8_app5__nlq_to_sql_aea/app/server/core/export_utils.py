import sqlite3
from typing import List, Dict
import pandas as pd
import io
import json
import base64


def generate_csv_from_data(data: List[Dict], columns: List[str]) -> bytes:
    """
    Generate CSV file from data and columns.
    
    Args:
        data: List of dictionaries containing the data
        columns: List of column names
        
    Returns:
        bytes: CSV file content as bytes
    """
    if not data and not columns:
        return b""
    
    if not columns and data:
        columns = list(data[0].keys()) if data else []
    
    df = pd.DataFrame(data, columns=columns)
    
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_content = csv_buffer.getvalue()
    csv_buffer.close()
    
    return csv_content.encode('utf-8')


def generate_csv_from_table(conn: sqlite3.Connection, table_name: str) -> bytes:
    """
    Generate CSV file from a database table.
    
    Args:
        conn: SQLite database connection
        table_name: Name of the table to export
        
    Returns:
        bytes: CSV file content as bytes
        
    Raises:
        ValueError: If table doesn't exist
    """
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name=?
    """, (table_name,))
    
    if not cursor.fetchone():
        raise ValueError(f"Table '{table_name}' does not exist")
    
    query = f'SELECT * FROM "{table_name}"'
    df = pd.read_sql_query(query, conn)
    
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_content = csv_buffer.getvalue()
    csv_buffer.close()
    
    return csv_content.encode('utf-8')


def generate_json_from_data(data: List[Dict], columns: List[str]) -> bytes:
    """
    Generate JSON file from data and columns.
    
    Args:
        data: List of dictionaries containing the data
        columns: List of column names
        
    Returns:
        bytes: JSON file content as bytes
    """
    if not data and not columns:
        return b"[]"
    
    if not columns and data:
        columns = list(data[0].keys()) if data else []
    
    # Ensure data only contains specified columns and handle special types
    filtered_data = []
    for row in data:
        filtered_row = {}
        for col in columns:
            value = row.get(col)
            # Handle bytes data
            if isinstance(value, bytes):
                filtered_row[col] = base64.b64encode(value).decode('utf-8')
            else:
                filtered_row[col] = value
        filtered_data.append(filtered_row)
    
    # Convert data to JSON with proper handling of special characters
    json_content = json.dumps(filtered_data, ensure_ascii=False, indent=2)
    
    return json_content.encode('utf-8')


def generate_json_from_table(conn: sqlite3.Connection, table_name: str) -> bytes:
    """
    Generate JSON file from a database table.
    
    Args:
        conn: SQLite database connection
        table_name: Name of the table to export
        
    Returns:
        bytes: JSON file content as bytes
        
    Raises:
        ValueError: If table doesn't exist
    """
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name=?
    """, (table_name,))
    
    if not cursor.fetchone():
        raise ValueError(f"Table '{table_name}' does not exist")
    
    # Get column names
    cursor.execute(f'PRAGMA table_info("{table_name}")')
    columns = [row[1] for row in cursor.fetchall()]
    
    # Get all data from table
    query = f'SELECT * FROM "{table_name}"'
    cursor.execute(query)
    rows = cursor.fetchall()
    
    # Convert rows to list of dictionaries
    data = []
    for row in rows:
        row_dict = {}
        for i, col in enumerate(columns):
            value = row[i]
            # Handle NULL values
            if value is None:
                row_dict[col] = None
            # Handle BLOB/bytes data
            elif isinstance(value, bytes):
                # Convert bytes to base64 string for JSON serialization
                row_dict[col] = base64.b64encode(value).decode('utf-8')
            else:
                row_dict[col] = value
        data.append(row_dict)
    
    # Convert to JSON
    json_content = json.dumps(data, ensure_ascii=False, indent=2)
    
    return json_content.encode('utf-8')
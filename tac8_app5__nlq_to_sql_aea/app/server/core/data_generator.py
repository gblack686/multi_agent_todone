import sqlite3
import random
import json
import logging
from typing import List, Dict, Any, Tuple
from core.llm_processor import generate_sql_with_openai, generate_sql_with_anthropic
from core.sql_security import validate_identifier, execute_query_safely, SQLSecurityError
from core.data_models import DataGenerationRequest, DataGenerationResponse
from core.utils import parse_json
import os

logger = logging.getLogger(__name__)


def sample_random_rows(conn: sqlite3.Connection, table_name: str, sample_size: int = 10) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Sample random rows from a table for pattern analysis.
    
    Args:
        conn: SQLite database connection
        table_name: Name of the table to sample from
        sample_size: Number of rows to sample (default 10)
        
    Returns:
        Tuple of (list of row dictionaries, list of column names)
        
    Raises:
        ValueError: If table doesn't exist or is empty
    """
    # Validate table name
    try:
        validate_identifier(table_name)
    except SQLSecurityError:
        raise ValueError(f"Invalid table name: {table_name}")
    
    # Get total row count
    count_query = f'SELECT COUNT(*) FROM [{table_name}]'
    cursor = execute_query_safely(conn, count_query)
    result = cursor.fetchone()
    total_rows = result[0] if result else 0
    
    if total_rows == 0:
        raise ValueError(f"Table '{table_name}' is empty")
    
    # Get column information
    cursor = conn.cursor()
    cursor.execute(f'PRAGMA table_info([{table_name}])')
    columns_info = cursor.fetchall()
    column_names = [col[1] for col in columns_info]
    
    # Sample rows
    if total_rows <= sample_size:
        # If table has fewer rows than sample size, return all rows
        query = f'SELECT * FROM [{table_name}]'
    else:
        # Use RANDOM() to get random sample
        query = f'SELECT * FROM [{table_name}] ORDER BY RANDOM() LIMIT {sample_size}'
    
    cursor = execute_query_safely(conn, query)
    rows = cursor.fetchall()
    
    # Convert to list of dictionaries
    sampled_data = []
    for row in rows:
        row_dict = {}
        for i, col_name in enumerate(column_names):
            row_dict[col_name] = row[i]
        sampled_data.append(row_dict)
    
    return sampled_data, column_names


def get_table_schema(conn: sqlite3.Connection, table_name: str) -> Dict[str, Any]:
    """
    Get detailed schema information for a table.
    
    Args:
        conn: SQLite database connection
        table_name: Name of the table
        
    Returns:
        Dictionary with schema information
    """
    try:
        validate_identifier(table_name)
    except SQLSecurityError:
        raise ValueError(f"Invalid table name: {table_name}")
    
    cursor = conn.cursor()
    cursor.execute(f'PRAGMA table_info([{table_name}])')
    columns_info = cursor.fetchall()
    
    schema = {
        'table_name': table_name,
        'columns': {}
    }
    
    for col in columns_info:
        col_name = col[1]
        schema['columns'][col_name] = {
            'type': col[2],
            'nullable': col[3] == 0,
            'default': col[4],
            'primary_key': col[5] == 1
        }
    
    return schema


def analyze_patterns_and_generate_data(sample_data: List[Dict[str, Any]], 
                                     schema: Dict[str, Any], 
                                     num_rows: int = 10) -> List[Dict[str, Any]]:
    """
    Analyze data patterns using LLM and generate synthetic data.
    
    Args:
        sample_data: Sample rows from the table
        schema: Table schema information
        num_rows: Number of rows to generate
        
    Returns:
        List of generated row dictionaries
    """
    # Prepare the prompt for LLM
    prompt = f"""Analyze the following table data and schema, then generate {num_rows} new synthetic rows that match the patterns.

Table Schema:
{json.dumps(schema, indent=2)}

Sample Data (showing patterns to follow):
{json.dumps(sample_data[:10], indent=2)}

Instructions:
1. Analyze the data types, formats, and patterns in each column
2. Understand relationships between columns if any
3. Identify value ranges and distributions
4. Recognize patterns like emails, phone numbers, addresses, dates, etc.
5. Generate {num_rows} new realistic rows that match these patterns
6. Ensure generated data respects nullable constraints
7. Make the data diverse but realistic

IMPORTANT: Return ONLY a valid JSON array with no additional text, explanation, or markdown.
The response must start with [ and end with ]
Do not include ```json or ``` or any other formatting.
Return exactly {num_rows} objects in this format: [{{"col1": "value1", "col2": "value2"}}, ...]"""

    try:
        # Try OpenAI first if available
        openai_key = os.environ.get("OPENAI_API_KEY")
        anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
        
        if openai_key:
            response = generate_data_with_openai(prompt)
        elif anthropic_key:
            response = generate_data_with_anthropic(prompt)
        else:
            raise ValueError("No LLM API key found")
        
        # Parse the response using the robust parse_json function
        try:
            generated_data = parse_json(response, target_type=list)
            
            if not isinstance(generated_data, list):
                raise ValueError("Generated data must be a JSON array")
            
            # Validate that we got the requested number of rows
            if len(generated_data) != num_rows:
                logger.warning(f"Generated {len(generated_data)} rows instead of {num_rows}")
            
            return generated_data
            
        except ValueError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.error(f"Original response was: {response}")
            
            # Provide a more helpful error message
            if "```" in response:
                raise ValueError("Failed to parse generated data as JSON - the model included markdown formatting. Please try again.")
            elif response.strip().startswith('{'):
                raise ValueError("Failed to parse generated data as JSON - expected an array but got an object. Please try again.")
            else:
                raise ValueError("Failed to parse generated data as JSON - the model response was not valid JSON. Please try again.")
            
    except Exception as e:
        logger.error(f"Error generating data with LLM: {e}")
        raise


def generate_data_with_openai(prompt: str) -> str:
    """Generate data using OpenAI."""
    from openai import OpenAI
    
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not set")
    
    client = OpenAI(api_key=api_key)
    
    # Enhanced system prompt to ensure JSON-only response
    system_prompt = """You are a JSON data generator. Your responses must be ONLY valid JSON arrays.
Rules:
1. Start your response with [ and end with ]
2. Do not include any text before or after the JSON array
3. Do not include markdown formatting like ```json or ```
4. Do not include explanations or comments
5. Generate only the requested JSON array of objects
6. Each object must have all required fields"""
    
    # Note: o4-mini model requires max_completion_tokens instead of max_tokens
    # and only supports temperature=1.0 (default)
    response = client.chat.completions.create(
        model="o4-mini-2025-04-16",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        temperature=1.0,
        max_completion_tokens=2000
    )
    
    content = response.choices[0].message.content.strip()
    
    # If the model returns a JSON object instead of an array, try to extract the array
    if content.startswith('{') and not content.startswith('['):
        try:
            obj = json.loads(content)
            # Look for common keys that might contain the array
            for key in ['data', 'rows', 'records', 'items', 'results']:
                if key in obj and isinstance(obj[key], list):
                    return json.dumps(obj[key])
        except:
            pass
    
    return content


def generate_data_with_anthropic(prompt: str) -> str:
    """Generate data using Anthropic."""
    from anthropic import Anthropic
    
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set")
    
    client = Anthropic(api_key=api_key)
    
    response = client.messages.create(
        model="claude-sonnet-4-0",
        max_tokens=2000,
        temperature=0.7,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    return response.content[0].text.strip()


def validate_generated_data(data: List[Dict[str, Any]], schema: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Validate generated data against schema constraints.
    
    Args:
        data: Generated data rows
        schema: Table schema
        
    Returns:
        Validated data rows
        
    Raises:
        ValueError: If validation fails
    """
    validated_data = []
    column_types = {col: info['type'] for col, info in schema['columns'].items()}
    
    for i, row in enumerate(data):
        validated_row = {}
        
        # Check that all required columns are present
        for col_name, col_info in schema['columns'].items():
            if col_name not in row and not col_info['nullable'] and col_info['default'] is None:
                raise ValueError(f"Row {i}: Missing required column '{col_name}'")
            
            # Get value or use None for nullable columns
            value = row.get(col_name)
            
            # Check nullable constraint
            if value is None and not col_info['nullable'] and col_info['default'] is None:
                raise ValueError(f"Row {i}: Column '{col_name}' cannot be null")
            
            # Basic type validation (SQLite is flexible with types)
            if value is not None:
                col_type = col_info['type'].upper()
                if 'INT' in col_type and not isinstance(value, (int, float)):
                    try:
                        value = int(value)
                    except (ValueError, TypeError):
                        raise ValueError(f"Row {i}: Invalid integer value for column '{col_name}': {value}")
                elif 'REAL' in col_type or 'FLOAT' in col_type or 'DOUBLE' in col_type:
                    if not isinstance(value, (int, float)):
                        try:
                            value = float(value)
                        except (ValueError, TypeError):
                            raise ValueError(f"Row {i}: Invalid numeric value for column '{col_name}': {value}")
            
            validated_row[col_name] = value
        
        validated_data.append(validated_row)
    
    return validated_data


def insert_generated_data(conn: sqlite3.Connection, table_name: str, data: List[Dict[str, Any]]) -> int:
    """
    Insert generated data into the table.
    
    Args:
        conn: SQLite database connection
        table_name: Name of the table
        data: Data rows to insert
        
    Returns:
        Number of rows inserted
        
    Raises:
        ValueError: If insertion fails
    """
    try:
        validate_identifier(table_name)
    except SQLSecurityError:
        raise ValueError(f"Invalid table name: {table_name}")
    
    if not data:
        return 0
    
    # Get column names from the first row
    columns = list(data[0].keys())
    
    # Validate all column names
    for col in columns:
        try:
            validate_identifier(col)
        except SQLSecurityError:
            raise ValueError(f"Invalid column name: {col}")
    
    # Build the INSERT query
    placeholders = ', '.join(['?' for _ in columns])
    column_names = ', '.join([f'[{col}]' for col in columns])
    query = f'INSERT INTO [{table_name}] ({column_names}) VALUES ({placeholders})'
    
    # Prepare values for insertion
    values_list = []
    for row in data:
        values = [row.get(col) for col in columns]
        values_list.append(values)
    
    # Execute batch insert
    cursor = conn.cursor()
    try:
        cursor.executemany(query, values_list)
        conn.commit()
        return cursor.rowcount
    except sqlite3.Error as e:
        conn.rollback()
        logger.error(f"Failed to insert data: {e}")
        raise ValueError(f"Failed to insert data: {e}")


def generate_table_data(conn: sqlite3.Connection, table_name: str) -> DataGenerationResponse:
    """
    Main function to generate and insert synthetic data for a table.
    
    Args:
        conn: SQLite database connection
        table_name: Name of the table
        
    Returns:
        DataGenerationResponse with generated rows and count
    """
    try:
        # Sample existing data
        sample_data, columns = sample_random_rows(conn, table_name)
        
        # Get table schema
        schema = get_table_schema(conn, table_name)
        
        # Generate synthetic data
        generated_data = analyze_patterns_and_generate_data(sample_data, schema)
        
        # Validate generated data
        validated_data = validate_generated_data(generated_data, schema)
        
        # Insert data into table
        rows_inserted = insert_generated_data(conn, table_name, validated_data)
        
        return DataGenerationResponse(
            success=True,
            rows_generated=rows_inserted,
            message=f"Successfully generated and inserted {rows_inserted} rows"
        )
        
    except Exception as e:
        logger.error(f"Error generating data for table '{table_name}': {e}")
        return DataGenerationResponse(
            success=False,
            rows_generated=0,
            message=str(e),
            error=str(e)
        )
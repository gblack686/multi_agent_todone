import pytest
import sqlite3
import json
from unittest.mock import patch, MagicMock
from core.data_generator import (
    sample_random_rows,
    get_table_schema,
    validate_generated_data,
    insert_generated_data,
    generate_table_data,
    analyze_patterns_and_generate_data
)
from core.data_models import DataGenerationResponse


class TestDataGenerator:
    
    @pytest.fixture
    def test_db(self):
        """Create a test database with sample data"""
        conn = sqlite3.connect(":memory:")
        cursor = conn.cursor()
        
        # Create test table
        cursor.execute("""
            CREATE TABLE test_users (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT,
                age INTEGER,
                created_at TEXT
            )
        """)
        
        # Insert sample data
        sample_data = [
            (1, 'John Doe', 'john@example.com', 25, '2024-01-01'),
            (2, 'Jane Smith', 'jane@example.com', 30, '2024-01-02'),
            (3, 'Bob Johnson', 'bob@example.com', 35, '2024-01-03'),
            (4, 'Alice Brown', 'alice@example.com', 28, '2024-01-04'),
            (5, 'Charlie Davis', 'charlie@example.com', 32, '2024-01-05')
        ]
        cursor.executemany(
            "INSERT INTO test_users VALUES (?, ?, ?, ?, ?)",
            sample_data
        )
        conn.commit()
        
        yield conn
        conn.close()
    
    def test_sample_random_rows_success(self, test_db):
        """Test sampling random rows from a table"""
        rows, columns = sample_random_rows(test_db, 'test_users', sample_size=3)
        
        assert len(rows) == 3
        assert len(columns) == 5
        assert columns == ['id', 'name', 'email', 'age', 'created_at']
        assert all(isinstance(row, dict) for row in rows)
        assert all('name' in row for row in rows)
    
    def test_sample_random_rows_empty_table(self, test_db):
        """Test sampling from an empty table"""
        cursor = test_db.cursor()
        cursor.execute("CREATE TABLE empty_table (id INTEGER)")
        test_db.commit()
        
        with pytest.raises(ValueError, match="Table 'empty_table' is empty"):
            sample_random_rows(test_db, 'empty_table')
    
    def test_sample_random_rows_invalid_table(self, test_db):
        """Test sampling from invalid table name"""
        with pytest.raises(ValueError, match="Invalid table name"):
            sample_random_rows(test_db, 'invalid-table!')
    
    def test_get_table_schema(self, test_db):
        """Test getting table schema information"""
        schema = get_table_schema(test_db, 'test_users')
        
        assert schema['table_name'] == 'test_users'
        assert len(schema['columns']) == 5
        assert 'id' in schema['columns']
        assert schema['columns']['id']['type'] == 'INTEGER'
        assert schema['columns']['id']['primary_key'] is True
        assert schema['columns']['name']['nullable'] is False
        assert schema['columns']['email']['nullable'] is True
    
    def test_validate_generated_data_success(self):
        """Test validation of correctly generated data"""
        schema = {
            'columns': {
                'id': {'type': 'INTEGER', 'nullable': False, 'default': None},
                'name': {'type': 'TEXT', 'nullable': False, 'default': None},
                'age': {'type': 'INTEGER', 'nullable': True, 'default': None}
            }
        }
        
        data = [
            {'id': 1, 'name': 'Test User', 'age': 25},
            {'id': 2, 'name': 'Another User', 'age': None}
        ]
        
        validated = validate_generated_data(data, schema)
        assert len(validated) == 2
        assert validated[0]['id'] == 1
        assert validated[1]['age'] is None
    
    def test_validate_generated_data_missing_required(self):
        """Test validation with missing required field"""
        schema = {
            'columns': {
                'id': {'type': 'INTEGER', 'nullable': False, 'default': None},
                'name': {'type': 'TEXT', 'nullable': False, 'default': None}
            }
        }
        
        data = [{'id': 1}]  # Missing required 'name'
        
        with pytest.raises(ValueError, match="Missing required column 'name'"):
            validate_generated_data(data, schema)
    
    def test_validate_generated_data_type_conversion(self):
        """Test type conversion during validation"""
        schema = {
            'columns': {
                'id': {'type': 'INTEGER', 'nullable': False, 'default': None},
                'price': {'type': 'REAL', 'nullable': True, 'default': None}
            }
        }
        
        data = [{'id': '123', 'price': '45.67'}]
        
        validated = validate_generated_data(data, schema)
        assert validated[0]['id'] == 123
        assert validated[0]['price'] == 45.67
    
    def test_insert_generated_data(self, test_db):
        """Test inserting generated data into table"""
        data = [
            {'name': 'New User 1', 'email': 'new1@example.com', 'age': 40},
            {'name': 'New User 2', 'email': 'new2@example.com', 'age': 45}
        ]
        
        rows_inserted = insert_generated_data(test_db, 'test_users', data)
        
        assert rows_inserted == 2
        
        # Verify data was inserted
        cursor = test_db.cursor()
        cursor.execute("SELECT COUNT(*) FROM test_users")
        count = cursor.fetchone()[0]
        assert count == 7  # 5 original + 2 new
    
    def test_insert_generated_data_invalid_column(self, test_db):
        """Test inserting data with invalid column"""
        data = [{'invalid_column': 'value'}]
        
        with pytest.raises(ValueError):
            insert_generated_data(test_db, 'test_users', data)
    
    @patch('core.data_generator.generate_data_with_openai')
    def test_analyze_patterns_and_generate_data_success(self, mock_openai):
        """Test pattern analysis and data generation with OpenAI"""
        sample_data = [
            {'id': 1, 'name': 'John Doe', 'email': 'john@example.com'},
            {'id': 2, 'name': 'Jane Smith', 'email': 'jane@example.com'}
        ]
        schema = {'table_name': 'users', 'columns': {}}
        
        # Mock LLM response
        mock_response = json.dumps([
            {'id': 3, 'name': 'Generated User', 'email': 'generated@example.com'},
            {'id': 4, 'name': 'Another Generated', 'email': 'another@example.com'}
        ])
        mock_openai.return_value = mock_response
        
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            result = analyze_patterns_and_generate_data(sample_data, schema, num_rows=2)
        
        assert len(result) == 2
        assert result[0]['name'] == 'Generated User'
        mock_openai.assert_called_once()
    
    @patch('core.data_generator.generate_data_with_anthropic')
    def test_analyze_patterns_and_generate_data_anthropic(self, mock_anthropic):
        """Test pattern analysis with Anthropic when OpenAI not available"""
        sample_data = [{'id': 1, 'name': 'Test'}]
        schema = {'table_name': 'test', 'columns': {}}
        
        mock_response = json.dumps([{'id': 2, 'name': 'Generated'}])
        mock_anthropic.return_value = mock_response
        
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'}, clear=True):
            result = analyze_patterns_and_generate_data(sample_data, schema, num_rows=1)
        
        assert len(result) == 1
        mock_anthropic.assert_called_once()
    
    def test_analyze_patterns_no_api_key(self):
        """Test error when no API key is available"""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="No LLM API key found"):
                analyze_patterns_and_generate_data([], {}, 1)
    
    @patch('core.data_generator.sample_random_rows')
    @patch('core.data_generator.get_table_schema')
    @patch('core.data_generator.analyze_patterns_and_generate_data')
    @patch('core.data_generator.validate_generated_data')
    @patch('core.data_generator.insert_generated_data')
    def test_generate_table_data_success(self, mock_insert, mock_validate, 
                                       mock_analyze, mock_schema, mock_sample, test_db):
        """Test complete data generation flow"""
        # Mock returns
        mock_sample.return_value = ([{'id': 1, 'name': 'Test'}], ['id', 'name'])
        mock_schema.return_value = {'table_name': 'test', 'columns': {}}
        mock_analyze.return_value = [{'id': 2, 'name': 'Generated'}]
        mock_validate.return_value = [{'id': 2, 'name': 'Generated'}]
        mock_insert.return_value = 1
        
        response = generate_table_data(test_db, 'test_table')
        
        assert response.success is True
        assert response.rows_generated == 1
        assert 'Successfully generated and inserted 1 rows' in response.message
        assert response.error is None
        
        # Verify all functions were called
        mock_sample.assert_called_once()
        mock_schema.assert_called_once()
        mock_analyze.assert_called_once()
        mock_validate.assert_called_once()
        mock_insert.assert_called_once()
    
    @patch('core.data_generator.sample_random_rows')
    def test_generate_table_data_empty_table(self, mock_sample, test_db):
        """Test error handling for empty table"""
        mock_sample.side_effect = ValueError("Table 'test_table' is empty")
        
        response = generate_table_data(test_db, 'test_table')
        
        assert response.success is False
        assert response.rows_generated == 0
        assert "Table 'test_table' is empty" in response.message
    
    @patch('core.data_generator.sample_random_rows')
    @patch('core.data_generator.get_table_schema')
    @patch('core.data_generator.analyze_patterns_and_generate_data')
    def test_generate_table_data_llm_error(self, mock_analyze, mock_schema, mock_sample, test_db):
        """Test error handling for LLM failures"""
        mock_sample.return_value = ([{'id': 1}], ['id'])
        mock_schema.return_value = {'table_name': 'test', 'columns': {}}
        mock_analyze.side_effect = ValueError("LLM API error")
        
        response = generate_table_data(test_db, 'test_table')
        
        assert response.success is False
        assert response.rows_generated == 0
        assert "LLM API error" in response.message
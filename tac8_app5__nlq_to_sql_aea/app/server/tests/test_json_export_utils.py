import pytest
import sqlite3
import json
from core.export_utils import generate_json_from_data, generate_json_from_table


class TestJSONExportUtils:
    
    def test_generate_json_from_data_empty(self):
        """Test JSON generation with empty data"""
        result = generate_json_from_data([], [])
        assert result == b"[]"
        
    def test_generate_json_from_data_with_columns_no_data(self):
        """Test JSON generation with columns but no data"""
        columns = ['id', 'name', 'value']
        result = generate_json_from_data([], columns)
        
        # Parse the JSON to verify
        json_data = json.loads(result.decode('utf-8'))
        
        assert json_data == []
        
    def test_generate_json_from_data_with_data(self):
        """Test JSON generation with actual data"""
        data = [
            {'id': 1, 'name': 'Test 1', 'value': 100},
            {'id': 2, 'name': 'Test 2', 'value': 200}
        ]
        columns = ['id', 'name', 'value']
        
        result = generate_json_from_data(data, columns)
        
        # Parse the JSON to verify
        json_data = json.loads(result.decode('utf-8'))
        
        assert len(json_data) == 2
        assert json_data[0]['id'] == 1
        assert json_data[0]['name'] == 'Test 1'
        assert json_data[0]['value'] == 100
        assert json_data[1]['id'] == 2
        assert json_data[1]['name'] == 'Test 2'
        assert json_data[1]['value'] == 200
        
    def test_generate_json_from_data_auto_columns(self):
        """Test JSON generation with automatic column detection"""
        data = [
            {'id': 1, 'name': 'Test 1'},
            {'id': 2, 'name': 'Test 2'}
        ]
        
        result = generate_json_from_data(data, [])
        
        # Parse the JSON to verify
        json_data = json.loads(result.decode('utf-8'))
        
        assert len(json_data) == 2
        assert 'id' in json_data[0]
        assert 'name' in json_data[0]
        assert json_data[0]['id'] == 1
        assert json_data[0]['name'] == 'Test 1'
        
    def test_generate_json_from_data_various_types(self):
        """Test JSON generation with various data types"""
        data = [
            {'int': 1, 'float': 1.5, 'string': 'test', 'bool': True, 'none': None},
            {'int': 2, 'float': 2.5, 'string': 'test2', 'bool': False, 'none': None}
        ]
        columns = ['int', 'float', 'string', 'bool', 'none']
        
        result = generate_json_from_data(data, columns)
        
        # Parse the JSON to verify
        json_data = json.loads(result.decode('utf-8'))
        
        assert json_data[0]['int'] == 1
        assert json_data[0]['float'] == 1.5
        assert json_data[0]['string'] == 'test'
        assert json_data[0]['bool'] is True
        assert json_data[0]['none'] is None
        assert json_data[1]['bool'] is False
        
    def test_generate_json_from_data_special_characters(self):
        """Test JSON generation with special characters"""
        data = [
            {'name': 'Test, with comma', 'desc': 'Quote "test"'},
            {'name': 'New\nline', 'desc': 'Tab\there'}
        ]
        columns = ['name', 'desc']
        
        result = generate_json_from_data(data, columns)
        
        # Parse the JSON to verify proper escaping
        json_data = json.loads(result.decode('utf-8'))
        
        assert json_data[0]['name'] == 'Test, with comma'
        assert json_data[0]['desc'] == 'Quote "test"'
        assert json_data[1]['name'] == 'New\nline'
        assert json_data[1]['desc'] == 'Tab\there'
        
    def test_generate_json_from_data_unicode(self):
        """Test JSON generation with Unicode characters"""
        data = [
            {'name': 'Test 测试', 'emoji': '😀🎉'},
            {'name': 'Café', 'emoji': '☕'}
        ]
        columns = ['name', 'emoji']
        
        result = generate_json_from_data(data, columns)
        
        # Parse the JSON to verify Unicode handling
        json_data = json.loads(result.decode('utf-8'))
        
        assert json_data[0]['name'] == 'Test 测试'
        assert json_data[0]['emoji'] == '😀🎉'
        assert json_data[1]['name'] == 'Café'
        assert json_data[1]['emoji'] == '☕'
        
    def test_generate_json_from_data_json_like_strings(self):
        """Test JSON generation with JSON-like strings"""
        data = [
            {'data': '{"nested": "json"}', 'array': '[1,2,3]'},
            {'data': '{}', 'array': '[]'}
        ]
        columns = ['data', 'array']
        
        result = generate_json_from_data(data, columns)
        
        # Parse the JSON to verify proper escaping
        json_data = json.loads(result.decode('utf-8'))
        
        assert json_data[0]['data'] == '{"nested": "json"}'
        assert json_data[0]['array'] == '[1,2,3]'
        assert json_data[1]['data'] == '{}'
        assert json_data[1]['array'] == '[]'
        
    def test_generate_json_from_data_column_filtering(self):
        """Test JSON generation filters to specified columns"""
        data = [
            {'id': 1, 'name': 'Test', 'secret': 'should not appear'},
            {'id': 2, 'name': 'Test2', 'secret': 'also hidden'}
        ]
        columns = ['id', 'name']  # Exclude 'secret' column
        
        result = generate_json_from_data(data, columns)
        
        # Parse the JSON to verify
        json_data = json.loads(result.decode('utf-8'))
        
        assert 'secret' not in json_data[0]
        assert 'secret' not in json_data[1]
        assert json_data[0]['id'] == 1
        assert json_data[0]['name'] == 'Test'
        
    def test_generate_json_from_table_nonexistent(self):
        """Test JSON generation from non-existent table"""
        # Create in-memory database
        conn = sqlite3.connect(':memory:')
        
        with pytest.raises(ValueError, match="Table 'nonexistent' does not exist"):
            generate_json_from_table(conn, 'nonexistent')
            
        conn.close()
        
    def test_generate_json_from_table_empty(self):
        """Test JSON generation from empty table"""
        # Create in-memory database with empty table
        conn = sqlite3.connect(':memory:')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE test_table (
                id INTEGER PRIMARY KEY,
                name TEXT,
                value REAL
            )
        ''')
        conn.commit()
        
        result = generate_json_from_table(conn, 'test_table')
        
        # Parse the JSON to verify
        json_data = json.loads(result.decode('utf-8'))
        
        assert json_data == []
        
        conn.close()
        
    def test_generate_json_from_table_with_data(self):
        """Test JSON generation from table with data"""
        # Create in-memory database with data
        conn = sqlite3.connect(':memory:')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE test_table (
                id INTEGER PRIMARY KEY,
                name TEXT,
                value REAL,
                created_date TEXT
            )
        ''')
        
        cursor.executemany('''
            INSERT INTO test_table (name, value, created_date) 
            VALUES (?, ?, ?)
        ''', [
            ('Item 1', 100.5, '2024-01-01'),
            ('Item 2', 200.75, '2024-01-02'),
            ('Item 3', None, '2024-01-03')
        ])
        conn.commit()
        
        result = generate_json_from_table(conn, 'test_table')
        
        # Parse the JSON to verify
        json_data = json.loads(result.decode('utf-8'))
        
        assert len(json_data) == 3
        assert json_data[0]['name'] == 'Item 1'
        assert json_data[0]['value'] == 100.5
        assert json_data[1]['value'] == 200.75
        assert json_data[2]['value'] is None
        assert json_data[2]['created_date'] == '2024-01-03'
        # Verify IDs are preserved
        assert json_data[0]['id'] == 1
        assert json_data[1]['id'] == 2
        assert json_data[2]['id'] == 3
        
        conn.close()
        
    def test_generate_json_from_table_special_name(self):
        """Test JSON generation from table with special characters in name"""
        # Create in-memory database
        conn = sqlite3.connect(':memory:')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE "special-table-name" (
                id INTEGER PRIMARY KEY,
                data TEXT
            )
        ''')
        
        cursor.execute('INSERT INTO "special-table-name" (data) VALUES (?)', ('test data',))
        conn.commit()
        
        result = generate_json_from_table(conn, 'special-table-name')
        
        # Parse the JSON to verify
        json_data = json.loads(result.decode('utf-8'))
        
        assert len(json_data) == 1
        assert json_data[0]['data'] == 'test data'
        assert json_data[0]['id'] == 1
        
        conn.close()
        
    def test_generate_json_from_table_mixed_types(self):
        """Test JSON generation from table with mixed data types"""
        # Create in-memory database
        conn = sqlite3.connect(':memory:')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE mixed_types (
                id INTEGER PRIMARY KEY,
                text_col TEXT,
                int_col INTEGER,
                real_col REAL,
                blob_col BLOB,
                null_col TEXT
            )
        ''')
        
        cursor.execute('''
            INSERT INTO mixed_types (text_col, int_col, real_col, blob_col, null_col) 
            VALUES (?, ?, ?, ?, ?)
        ''', ('text', 42, 3.14, b'binary data', None))
        conn.commit()
        
        result = generate_json_from_table(conn, 'mixed_types')
        
        # Parse the JSON to verify
        json_data = json.loads(result.decode('utf-8'))
        
        assert len(json_data) == 1
        assert json_data[0]['text_col'] == 'text'
        assert json_data[0]['int_col'] == 42
        assert json_data[0]['real_col'] == 3.14
        assert json_data[0]['null_col'] is None
        # SQLite returns BLOB as bytes, which should be handled
        assert isinstance(json_data[0]['blob_col'], (str, bytes))
        
        conn.close()
        
    def test_generate_json_schema_validation(self):
        """Test that generated JSON is valid and well-formatted"""
        data = [
            {'id': 1, 'name': 'Test 1', 'value': 100},
            {'id': 2, 'name': 'Test 2', 'value': 200}
        ]
        columns = ['id', 'name', 'value']
        
        result = generate_json_from_data(data, columns)
        json_str = result.decode('utf-8')
        
        # Verify it's pretty-printed (has indentation)
        assert '\n' in json_str
        assert '  ' in json_str  # Has indentation
        
        # Verify it can be parsed and re-serialized
        parsed = json.loads(json_str)
        re_serialized = json.dumps(parsed, ensure_ascii=False, indent=2)
        
        # Should be able to parse the re-serialized version
        json.loads(re_serialized)
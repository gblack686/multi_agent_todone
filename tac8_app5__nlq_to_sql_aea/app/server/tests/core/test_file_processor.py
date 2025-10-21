import pytest
from pathlib import Path
from core.file_processor import convert_csv_to_sqlite, convert_json_to_sqlite, convert_jsonl_to_sqlite, flatten_json_object, discover_jsonl_fields


@pytest.fixture
def test_db():
    """Return path for in-memory test database"""
    return ':memory:'


@pytest.fixture
def test_assets_dir():
    """Get the path to test assets directory"""
    return Path(__file__).parent.parent / "assets"


class TestFileProcessor:
    
    def test_convert_csv_to_sqlite_success(self, test_db, test_assets_dir):
        # Load real CSV file
        csv_file = test_assets_dir / "test_users.csv"
        with open(csv_file, 'rb') as f:
            csv_data = f.read()
        
        table_name = "users"
        result = convert_csv_to_sqlite(csv_data, table_name, test_db)
        
        # Verify return structure
        assert result['table_name'] == table_name
        assert 'schema' in result
        assert 'row_count' in result
        assert 'sample_data' in result
        
        # Test the returned data
        assert result['row_count'] == 4  # 4 users in test file
        assert len(result['sample_data']) <= 5  # Should return up to 5 samples
        
        # Verify schema has expected columns (cleaned names)
        assert 'name' in result['schema']
        assert 'age' in result['schema'] 
        assert 'city' in result['schema']
        assert 'email' in result['schema']
        
        # Verify sample data structure and content
        john_data = next((item for item in result['sample_data'] if item['name'] == 'John Doe'), None)
        assert john_data is not None
        assert john_data['age'] == 25
        assert john_data['city'] == 'New York'
        assert john_data['email'] == 'john@example.com'
    
    def test_convert_csv_to_sqlite_column_cleaning(self, test_db, test_assets_dir):
        # Test column name cleaning with real file
        csv_file = test_assets_dir / "column_names.csv"
        with open(csv_file, 'rb') as f:
            csv_data = f.read()
        
        table_name = "test_users"
        result = convert_csv_to_sqlite(csv_data, table_name, test_db)
        
        # Verify columns were cleaned in the schema
        assert 'full_name' in result['schema']
        assert 'birth_date' in result['schema']
        assert 'email_address' in result['schema']
        assert 'phone_number' in result['schema']
        
        # Verify sample data has cleaned column names and actual content
        sample = result['sample_data'][0]
        assert 'full_name' in sample
        assert 'birth_date' in sample
        assert 'email_address' in sample
        assert sample['full_name'] == 'John Doe'
        assert sample['birth_date'] == '1990-01-15'
    
    def test_convert_csv_to_sqlite_with_inconsistent_data(self, test_db, test_assets_dir):
        # Test with CSV that has inconsistent row lengths - should raise error
        csv_file = test_assets_dir / "invalid.csv"
        with open(csv_file, 'rb') as f:
            csv_data = f.read()
        
        table_name = "inconsistent_table"
        
        # Pandas will fail on inconsistent CSV data
        with pytest.raises(Exception) as exc_info:
            convert_csv_to_sqlite(csv_data, table_name, test_db)
        
        assert "Error converting CSV to SQLite" in str(exc_info.value)
    
    def test_convert_json_to_sqlite_success(self, test_db, test_assets_dir):
        # Load real JSON file
        json_file = test_assets_dir / "test_products.json"
        with open(json_file, 'rb') as f:
            json_data = f.read()
        
        table_name = "products"
        result = convert_json_to_sqlite(json_data, table_name, test_db)
        
        # Verify return structure
        assert result['table_name'] == table_name
        assert 'schema' in result
        assert 'row_count' in result
        assert 'sample_data' in result
        
        # Test the returned data
        assert result['row_count'] == 3  # 3 products in test file
        assert len(result['sample_data']) == 3
        
        # Verify schema has expected columns
        assert 'id' in result['schema']
        assert 'name' in result['schema']
        assert 'price' in result['schema']
        assert 'category' in result['schema']
        assert 'in_stock' in result['schema']
        
        # Verify sample data structure and content
        laptop_data = next((item for item in result['sample_data'] if item['name'] == 'Laptop'), None)
        assert laptop_data is not None
        assert laptop_data['price'] == 999.99
        assert laptop_data['category'] == 'Electronics'
        assert laptop_data['in_stock']
    
    def test_convert_json_to_sqlite_invalid_json(self, test_db):
        # Test with invalid JSON
        json_data = b'invalid json'
        table_name = "test_table"
        
        with pytest.raises(Exception) as exc_info:
            convert_json_to_sqlite(json_data, table_name, test_db)
        
        assert "Error converting JSON to SQLite" in str(exc_info.value)
    
    def test_convert_json_to_sqlite_not_array(self, test_db):
        # Test with JSON that's not an array
        json_data = b'{"name": "John", "age": 25}'
        table_name = "test_table"
        
        with pytest.raises(Exception) as exc_info:
            convert_json_to_sqlite(json_data, table_name, test_db)
        
        assert "JSON must be an array of objects" in str(exc_info.value)
    
    def test_convert_json_to_sqlite_empty_array(self, test_db):
        # Test with empty JSON array
        json_data = b'[]'
        table_name = "test_table"
        
        with pytest.raises(Exception) as exc_info:
            convert_json_to_sqlite(json_data, table_name, test_db)
        
        assert "JSON array is empty" in str(exc_info.value)
    
    def test_flatten_json_object_nested_dict(self):
        """Test flattening nested dictionary objects"""
        obj = {
            "user": {
                "profile": {
                    "name": "John",
                    "age": 30
                }
            }
        }
        
        flattened = flatten_json_object(obj)
        
        assert flattened["user__profile__name"] == "John"
        assert flattened["user__profile__age"] == 30
    
    def test_flatten_json_object_array(self):
        """Test flattening arrays with indices"""
        obj = {
            "items": ["apple", "banana", "cherry"]
        }
        
        flattened = flatten_json_object(obj)
        
        assert flattened["items_0"] == "apple"
        assert flattened["items_1"] == "banana"
        assert flattened["items_2"] == "cherry"
    
    def test_flatten_json_object_complex(self):
        """Test flattening complex nested structure with arrays and objects"""
        obj = {
            "user": {
                "name": "Alice",
                "tags": ["admin", "user"]
            },
            "actions": [
                {"type": "login", "timestamp": "2023-01-01"},
                {"type": "logout", "timestamp": "2023-01-02"}
            ]
        }
        
        flattened = flatten_json_object(obj)
        
        assert flattened["user__name"] == "Alice"
        assert flattened["user__tags_0"] == "admin"
        assert flattened["user__tags_1"] == "user"
        assert flattened["actions_0__type"] == "login"
        assert flattened["actions_0__timestamp"] == "2023-01-01"
        assert flattened["actions_1__type"] == "logout"
        assert flattened["actions_1__timestamp"] == "2023-01-02"
    
    def test_flatten_json_object_primitive(self):
        """Test flattening primitive values"""
        assert flatten_json_object("hello") == {"": "hello"}
        assert flatten_json_object(42) == {"": 42}
        assert flatten_json_object(True) == {"": True}
        assert flatten_json_object(None) == {"": None}
    
    def test_discover_jsonl_fields_basic(self):
        """Test field discovery with basic JSONL content"""
        jsonl_content = b'{"name": "John", "age": 30}\n{"name": "Jane", "age": 25, "city": "NYC"}'
        
        fields = discover_jsonl_fields(jsonl_content)
        
        assert fields == {"name", "age", "city"}
    
    def test_discover_jsonl_fields_nested(self):
        """Test field discovery with nested structures"""
        jsonl_content = b'{"user": {"name": "John", "profile": {"age": 30}}}\n{"user": {"name": "Jane", "profile": {"city": "NYC"}}}'
        
        fields = discover_jsonl_fields(jsonl_content)
        
        assert fields == {"user__name", "user__profile__age", "user__profile__city"}
    
    def test_discover_jsonl_fields_arrays(self):
        """Test field discovery with arrays"""
        jsonl_content = b'{"items": ["a", "b"]}\n{"items": ["c", "d", "e"]}'
        
        fields = discover_jsonl_fields(jsonl_content)
        
        assert fields == {"items_0", "items_1", "items_2"}
    
    def test_discover_jsonl_fields_invalid_json(self):
        """Test field discovery with invalid JSON"""
        jsonl_content = b'{"valid": "json"}\n{invalid json}'
        
        with pytest.raises(ValueError) as exc_info:
            discover_jsonl_fields(jsonl_content)
        
        assert "Invalid JSON on line 2" in str(exc_info.value)
    
    def test_discover_jsonl_fields_empty_lines(self):
        """Test field discovery with empty lines"""
        jsonl_content = b'{"name": "John"}\n\n{"name": "Jane"}\n'
        
        fields = discover_jsonl_fields(jsonl_content)
        
        assert fields == {"name"}
    
    def test_convert_jsonl_to_sqlite_success(self, test_db, test_assets_dir):
        """Test successful JSONL to SQLite conversion with real file"""
        jsonl_file = test_assets_dir / "sample_data.jsonl"
        with open(jsonl_file, 'rb') as f:
            jsonl_data = f.read()
        
        table_name = "users"
        result = convert_jsonl_to_sqlite(jsonl_data, table_name, test_db)
        
        # Verify return structure
        assert result['table_name'] == table_name
        assert 'schema' in result
        assert 'row_count' in result
        assert 'sample_data' in result
        
        # Test the returned data
        assert result['row_count'] == 5  # 5 users in test file
        assert len(result['sample_data']) <= 5  # Should return up to 5 samples
        
        # Verify schema has expected columns (both flat and nested)
        assert 'id' in result['schema']
        assert 'name' in result['schema']
        assert 'email' in result['schema']
        assert 'age' in result['schema']
        assert 'active' in result['schema']
        assert 'profile__bio' in result['schema']
        assert 'profile__location' in result['schema']
        assert 'profile__skills_0' in result['schema']
        assert 'profile__skills_1' in result['schema']
        assert 'metadata__created_at' in result['schema']
        assert 'metadata__updated_at' in result['schema']
        
        # Verify sample data structure and content
        john_data = next((item for item in result['sample_data'] if item['name'] == 'John Doe'), None)
        assert john_data is not None
        assert john_data['id'] == 1
        assert john_data['email'] == 'john@example.com'
        assert john_data['age'] == 30
        assert john_data['active'] == 1  # SQLite stores boolean as integer
        
        # Verify flattened nested data
        alice_data = next((item for item in result['sample_data'] if item['name'] == 'Alice Brown'), None)
        assert alice_data is not None
        assert alice_data['profile__bio'] == 'Data scientist'
        assert alice_data['profile__location'] == 'SF'
        assert alice_data['profile__skills_0'] == 'Python'
        assert alice_data['profile__skills_1'] == 'Machine Learning'
    
    def test_convert_jsonl_to_sqlite_complex(self, test_db, test_assets_dir):
        """Test JSONL to SQLite conversion with complex nested structures"""
        jsonl_file = test_assets_dir / "complex_data.jsonl"
        with open(jsonl_file, 'rb') as f:
            jsonl_data = f.read()
        
        table_name = "events"
        result = convert_jsonl_to_sqlite(jsonl_data, table_name, test_db)
        
        # Verify return structure
        assert result['table_name'] == table_name
        assert result['row_count'] == 5  # 5 events in test file
        
        # Verify complex nested fields are flattened
        assert 'user__id' in result['schema']
        assert 'user__name' in result['schema']
        assert 'user__profile__email' in result['schema']
        assert 'user__profile__preferences__theme' in result['schema']
        assert 'user__profile__preferences__notifications' in result['schema']
        assert 'actions_0__type' in result['schema']
        assert 'actions_0__timestamp' in result['schema']
        assert 'actions_0__amount' in result['schema']
        assert 'tags_0' in result['schema']
        assert 'tags_1' in result['schema']
        assert 'metadata__source' in result['schema']
        assert 'metadata__device' in result['schema']
        assert 'nested__deep__very__nested__value' in result['schema']
        
        # Verify sample data with complex structures
        alice_event = next((item for item in result['sample_data'] if item['event_id'] == 'evt_001'), None)
        assert alice_event is not None
        assert alice_event['user__id'] == 123
        assert alice_event['user__name'] == 'Alice'
        assert alice_event['user__profile__email'] == 'alice@test.com'
        assert alice_event['user__profile__preferences__theme'] == 'dark'
        assert alice_event['user__profile__preferences__notifications'] == 1  # Boolean as integer
        assert alice_event['actions_0__type'] == 'click'
        assert alice_event['actions_1__type'] == 'view'
        assert alice_event['metadata__source'] == 'web'
        assert alice_event['metadata__device'] == 'desktop'
    
    def test_convert_jsonl_to_sqlite_invalid_json(self, test_db):
        """Test JSONL conversion with invalid JSON"""
        jsonl_data = b'{"valid": "json"}\n{invalid json}'
        table_name = "test_table"
        
        with pytest.raises(Exception) as exc_info:
            convert_jsonl_to_sqlite(jsonl_data, table_name, test_db)
        
        assert "Invalid JSON on line 2" in str(exc_info.value)
    
    def test_convert_jsonl_to_sqlite_empty_file(self, test_db):
        """Test JSONL conversion with empty file"""
        jsonl_data = b''
        table_name = "test_table"
        
        with pytest.raises(Exception) as exc_info:
            convert_jsonl_to_sqlite(jsonl_data, table_name, test_db)
        
        assert "No valid JSON objects found in JSONL file" in str(exc_info.value)
    
    def test_convert_jsonl_to_sqlite_blank_lines_only(self, test_db):
        """Test JSONL conversion with only blank lines"""
        jsonl_data = b'\n\n\n'
        table_name = "test_table"
        
        with pytest.raises(Exception) as exc_info:
            convert_jsonl_to_sqlite(jsonl_data, table_name, test_db)
        
        assert "No valid JSON objects found in JSONL file" in str(exc_info.value)
    
    def test_convert_jsonl_to_sqlite_inconsistent_schema(self, test_db):
        """Test JSONL conversion with inconsistent schema across lines"""
        jsonl_data = b'{"name": "John", "age": 30}\n{"name": "Jane", "city": "NYC", "profile": {"bio": "Engineer"}}'
        table_name = "test_table"
        
        result = convert_jsonl_to_sqlite(jsonl_data, table_name, test_db)
        
        # Should handle inconsistent schema by including all fields
        assert 'name' in result['schema']
        assert 'age' in result['schema']
        assert 'city' in result['schema']
        assert 'profile__bio' in result['schema']
        
        # First record should have None for missing fields
        john_data = next((item for item in result['sample_data'] if item['name'] == 'John'), None)
        assert john_data is not None
        assert john_data['age'] == 30
        assert john_data['city'] is None
        assert john_data['profile__bio'] is None
        
        # Second record should have None for missing fields
        jane_data = next((item for item in result['sample_data'] if item['name'] == 'Jane'), None)
        assert jane_data is not None
        assert jane_data['age'] is None
        assert jane_data['city'] == 'NYC'
        assert jane_data['profile__bio'] == 'Engineer'
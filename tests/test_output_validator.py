import json
import pytest
from unittest.mock import AsyncMock, patch

from open_notebook.ai.validator import OutputSchemaValidator
from open_notebook.exceptions import SchemaValidationError


@pytest.fixture
def test_schema():
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"}
        },
        "required": ["name", "age"],
        "additionalProperties": False
    }

@pytest.fixture
def mock_schema_file(tmp_path, test_schema):
    schema_path = tmp_path / "test.schema.json"
    with open(schema_path, "w") as f:
        json.dump(test_schema, f)
    return str(schema_path)

@pytest.fixture
def validator(mock_schema_file):
    return OutputSchemaValidator(mock_schema_file)

@pytest.mark.asyncio
async def test_valid_json(validator):
    """Test 1: Valid JSON should pass directly without fixing."""
    valid_input = '{"name": "Alice", "age": 30}'
    with patch.object(validator, '_schema_fix') as mock_fix:
        result = await validator.validate_and_fix(valid_input)
        assert result == {"name": "Alice", "age": 30}
        mock_fix.assert_not_called()

@pytest.mark.asyncio
async def test_broken_json_fixed(validator):
    """Test 2: Malformed JSON missing properties gets fixed successfully."""
    invalid_input = '{"name": "Alice"}' # Missing 'age'
    
    # Mock the LLM to return a valid fixed JSON string on the first attempt
    async def mock_schema_fix_func(raw_input, errors):
        return '{"name": "Alice", "age": 25}'
        
    with patch.object(validator, '_schema_fix', side_effect=mock_schema_fix_func) as mock_fix:
        result = await validator.validate_and_fix(invalid_input)
        assert result == {"name": "Alice", "age": 25}
        assert mock_fix.call_count == 1

@pytest.mark.asyncio
async def test_irrecoverable_json(validator):
    """Test 3: Completely broken schema raises SchemaValidationError after max_retries."""
    invalid_input = '{"name": "Alice"}'
    
    # Mock the LLM to continuously fail, returning invalid JSON
    async def mock_schema_fix_func(raw_input, errors):
        return '{"name": "Alice", "random_field": "still bad"}'
        
    with patch.object(validator, '_schema_fix', side_effect=mock_schema_fix_func) as mock_fix:
        with pytest.raises(SchemaValidationError) as exc:
            await validator.validate_and_fix(invalid_input, max_retries=2)
        
        # Original call + 2 retries = 3 validations total. 2 schema_fix calls since max_retries=2.
        assert mock_fix.call_count == 2
        assert exc.value.retries_used == 2
        assert exc.value.error_code == "SCHEMA_VALIDATION_FAILED"
        assert "random_field" in str(exc.value.errors)

@pytest.mark.asyncio
async def test_extra_fields_removed(validator):
    """Test 4: Extra hallucinated fields must be caught since additionalProperties=False."""
    invalid_input = '{"name": "Alice", "age": 30, "hallucinated_field": True}'
    
    async def mock_schema_fix_func(raw_input, errors):
        return '{"name": "Alice", "age": 30}'
        
    with patch.object(validator, '_schema_fix', side_effect=mock_schema_fix_func) as mock_fix:
        result = await validator.validate_and_fix(invalid_input)
        assert result == {"name": "Alice", "age": 30}
        assert mock_fix.call_count == 1

@pytest.mark.asyncio
async def test_json_wrapped_in_text(validator):
    """Test 5: Extractor should ignore conversational markdown or prefixes."""
    wrapped_input = '''Sure, here is your JSON output format:
```json
{
  "name": "Bob",
  "age": 42
}
```
Thanks for asking!'''
    
    with patch.object(validator, '_schema_fix') as mock_fix:
        result = await validator.validate_and_fix(wrapped_input)
        assert result == {"name": "Bob", "age": 42}
        mock_fix.assert_not_called()

@pytest.mark.asyncio
async def test_json_wrapped_in_text_no_codeblocks(validator):
    """Test 5b: Extractor should handle text prefix WITHOUT markdown blocks."""
    wrapped_input = '''Sure, here is your JSON output format:
{
  "name": "Charlie",
  "age": 42
}
Hope this helps!'''
    
    with patch.object(validator, '_schema_fix') as mock_fix:
        result = await validator.validate_and_fix(wrapped_input)
        assert result == {"name": "Charlie", "age": 42}
        mock_fix.assert_not_called()

@pytest.mark.asyncio
async def test_nested_field_violation(validator):
    """Test 6: Internal schema structural validation checking."""
    # Test strict typing on age (integer vs float)
    invalid_input = '{"name": "Charlie", "age": 42.5}'
    
    async def mock_schema_fix_func(raw_input, errors):
        return '{"name": "Charlie", "age": 42}'
        
    with patch.object(validator, '_schema_fix', side_effect=mock_schema_fix_func) as mock_fix:
        result = await validator.validate_and_fix(invalid_input)
        assert result == {"name": "Charlie", "age": 42}
        assert mock_fix.call_count == 1

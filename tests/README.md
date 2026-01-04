# Notev Unit Tests

This directory contains unit tests for the Notev application.

## Test Coverage

### Core Modules
- **test_document_processor.py**: Tests for document text extraction, chunking, and validation ✓
- **test_vector_store.py**: Tests for in-memory vector storage and search ✓
- **test_workspace_manager.py**: Tests for workspace CRUD operations and conversation management ✓
- **test_api.py**: ~~API endpoint tests~~ (Disabled - would interfere with real data)

**Note on API Tests:** The API tests are currently disabled because they were creating test workspaces in the actual application storage, causing test events to appear in the UI. For API testing, use manual testing or create a separate test environment.

## Running Tests

### Run All Tests

Using the test runner:
```bash
python run_tests.py
```

Using pytest (recommended):
```bash
pytest tests/
```

With coverage report:
```bash
pytest tests/ --cov=notev_backend --cov-report=html
```

### Run Specific Test Module

Using the test runner:
```bash
python run_tests.py test_document_processor
```

Using pytest:
```bash
pytest tests/test_document_processor.py
```

Using unittest:
```bash
python -m unittest tests.test_document_processor
```

### Run Specific Test Case

```bash
pytest tests/test_document_processor.py::TestDocumentProcessor::test_create_chunks_basic
```

## Test Structure

Each test file follows this pattern:
1. **setUp()**: Create test fixtures before each test
2. **tearDown()**: Clean up after each test
3. **test_xxx()**: Individual test methods

## Writing New Tests

When adding new features, follow these guidelines:

1. Create a new test file if testing a new module
2. Name test files as `test_<module_name>.py`
3. Name test methods as `test_<what_it_tests>()`
4. Use descriptive docstrings
5. Clean up resources in tearDown()

Example:
```python
def test_new_feature(self):
    """Test that new feature works correctly."""
    # Arrange
    input_data = "test"

    # Act
    result = my_function(input_data)

    # Assert
    self.assertEqual(result, expected_value)
```

## Current Test Coverage

- Document Processing: ✓ Text extraction, chunking, validation
- Vector Store: ✓ Add, remove, search, filter
- Workspace Manager: ✓ CRUD, conversations
- API Endpoints: ✓ Basic workspace operations

## TODO: Additional Tests

- [ ] Document upload with real files (docx, pptx, pdf)
- [ ] Chat agent response generation
- [ ] Global documents manager
- [ ] File permissions handling
- [ ] Hebrew/RTL text processing
- [ ] Conflict detection
- [ ] Integration tests with full workflow

## Dependencies

Tests require:
- pytest
- pytest-cov (for coverage reports)

Install with:
```bash
pip install pytest pytest-cov
```

## CI/CD Integration

These tests can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions
- name: Run tests
  run: pytest tests/ --cov=notev_backend
```

## Notes

- Tests use temporary directories that are cleaned up automatically
- API tests run in test mode (no actual API calls to Anthropic)
- Vector store tests use mock embeddings

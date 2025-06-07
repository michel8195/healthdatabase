# Testing Guide for Health Data Analytics System

This document explains the testing strategy, types of tests, and best practices for the health data analytics system.

## Table of Contents
1. [Testing Philosophy](#testing-philosophy)
2. [Types of Tests](#types-of-tests)
3. [Test Structure and Organization](#test-structure-and-organization)
4. [Testing Tools and Configuration](#testing-tools-and-configuration)
5. [When to Write Which Type of Test](#when-to-write-which-type-of-test)
6. [Testing Best Practices](#testing-best-practices)
7. [Understanding Test Results](#understanding-test-results)
8. [Common Testing Patterns](#common-testing-patterns)

## Testing Philosophy

### Why Test?
Testing serves several critical purposes:
- **Verify functionality**: Ensure your code does what it's supposed to do
- **Prevent regressions**: Catch when changes break existing functionality
- **Enable refactoring**: Change code confidently knowing tests will catch issues
- **Document behavior**: Tests serve as examples of how code should work
- **Improve design**: Writing tests often reveals design problems

### Testing Pyramid
Our testing strategy follows the testing pyramid concept:

```
    /\
   /  \     End-to-End Tests (Few)
  /____\    - Full system workflows
 /      \   - User scenarios
/        \  
/__________\ Integration Tests (Some)
|          | - Module interactions
|          | - Database operations
|          | - File processing
|__________|
|          |
|          | Unit Tests (Many)
|          | - Individual functions
|          | - Data validation
|          | - Business logic
|__________|
```

**Bottom Heavy**: Most tests should be fast, isolated unit tests. Fewer integration tests. Minimal end-to-end tests.

## Types of Tests

### 1. Unit Tests (Most Important)
**What they test**: Individual functions, methods, or small components in isolation.

**Examples in our codebase**:
```python
def test_validate_data_valid(self, activity_model, sample_activity_data):
    """Test that valid data is properly validated"""
    validated = activity_model.validate_data(sample_activity_data)
    assert validated['user_id'] == 1
    assert validated['steps'] == 8500
```

**Characteristics**:
- ✅ **Fast** (milliseconds)
- ✅ **Isolated** (no external dependencies)
- ✅ **Reliable** (same result every time)
- ✅ **Easy to debug** (small scope)

**When to write**:
- For every business logic function
- For data validation
- For utility functions
- For error handling

### 2. Integration Tests (Secondary)
**What they test**: How multiple components work together.

**Examples in our codebase**:
```python
def test_activity_import_integration(self, initialized_db, test_csv_file):
    """Test complete import workflow"""
    importer = ZeppActivityImporter(initialized_db)
    stats = importer.import_file(test_csv_file, user_id=1, dry_run=True)
    assert stats['processed'] == 3
    assert stats['errors'] == 0
```

**Characteristics**:
- ⚠️ **Slower** (seconds)
- ⚠️ **Dependencies** (database, files)
- ⚠️ **More complex** (multiple moving parts)
- ✅ **Realistic** (tests real scenarios)

**When to write**:
- For critical workflows
- For database operations
- For file processing
- For API endpoints

### 3. End-to-End Tests (Least)
**What they test**: Complete user workflows from start to finish.

**Example scenario**:
```python
def test_complete_data_import_workflow():
    """Test: User imports CSV file and analyzes data"""
    # 1. Setup database
    # 2. Import CSV file
    # 3. Query data
    # 4. Generate analysis
    # 5. Verify results
```

**Characteristics**:
- ❌ **Slow** (minutes)
- ❌ **Brittle** (many failure points)
- ❌ **Hard to debug** (complex interactions)
- ✅ **High confidence** (tests real user scenarios)

**When to write**:
- For critical user journeys
- For release verification
- For smoke tests

## Test Structure and Organization

### Directory Structure
```
tests/
├── conftest.py              # Shared fixtures and configuration
├── test_models.py           # Unit tests for database models
├── test_importers.py        # Unit + integration tests for importers
├── test_database.py         # Integration tests for database operations
└── test_bulk_import.py      # Integration tests for bulk operations
```

### conftest.py Location
The `conftest.py` file should be placed in the `tests/` directory, not in the project root:

**✅ Correct placement:**
```
project/
├── src/
├── tests/
│   ├── conftest.py          # ← Here (scoped to tests only)
│   ├── test_models.py
│   └── ...
```

**❌ Incorrect placement:**
```
project/
├── conftest.py              # ← Not here (too broad scope)
├── src/
├── tests/
```

**Why this matters:**
- **Scope control**: Only loads fixtures when running tests
- **Performance**: Faster imports during normal application usage
- **Convention**: Standard pytest practice
- **Clarity**: Clear separation between test and application code

### Test Naming Convention
```python
class TestClassName:
    def test_function_name_scenario(self):
        """Test description explaining what is being tested"""
```

**Examples**:
- `test_validate_data_valid` - Tests validation with valid data
- `test_validate_data_missing_required` - Tests validation with missing required fields
- `test_import_file_corrupted_csv` - Tests import with corrupted CSV file

### Fixtures (Test Data Setup)
Fixtures provide reusable test data and setup:

```python
@pytest.fixture
def sample_activity_data():
    """Sample activity data for testing"""
    return {
        'user_id': 1,
        'date': '2024-01-15',
        'steps': 8500,
        'calories': 2200.5
    }
```

**Benefits**:
- ✅ **Reusable** across multiple tests
- ✅ **Consistent** data for reliable tests
- ✅ **Clean** separation of test data from test logic

## Testing Tools and Configuration

### pytest Configuration (`pytest.ini`)
```ini
[tool:pytest]
testpaths = tests              # Where to find tests
python_files = test_*.py       # Test file naming pattern
addopts = -v --tb=short       # Verbose output, short tracebacks
markers =                      # Custom test categories
    unit: Unit tests
    integration: Integration tests
    slow: Slow tests
    database: Tests requiring database
```

### Test Markers (Categories)
```python
@pytest.mark.unit          # Fast, isolated tests
@pytest.mark.integration   # Multi-component tests
@pytest.mark.database      # Tests needing database
@pytest.mark.slow          # Long-running tests
```

### Running Tests
```bash
# Run all tests
pytest

# Run only unit tests (fastest)
pytest -m unit

# Run with coverage report
pytest --cov=src

# Run specific test file
pytest tests/test_models.py

# Run and stop on first failure
pytest -x
```

## When to Write Which Type of Test

### Priority 1: Unit Tests
**Write unit tests when**:
- You have business logic to validate
- You need to test error conditions
- You want to verify data transformations
- You have utility functions

**Example scenarios**:
```python
# Data validation
def test_activity_model_validates_negative_steps():
    # Should convert negative steps to 0
    
# Error handling  
def test_importer_handles_invalid_csv():
    # Should raise appropriate exception

# Business logic
def test_sleep_efficiency_calculation():
    # Should calculate percentage correctly
```

### Priority 2: Integration Tests
**Write integration tests when**:
- You need to test workflows
- Multiple components interact
- You use external systems (database, files)
- You want to test configuration

**Example scenarios**:
```python
# Database operations
def test_bulk_import_with_duplicates():
    # Should handle duplicate records properly
    
# File processing
def test_csv_import_end_to_end():
    # Should import CSV and store in database

# Workflow testing
def test_complete_data_analysis_pipeline():
    # Should process data from import to analysis
```

### Priority 3: End-to-End Tests
**Write E2E tests when**:
- You need to verify critical user journeys
- You want smoke tests for releases
- You need to test system configuration
- You want to catch integration issues

## Testing Best Practices

### 1. Test Structure (AAA Pattern)
```python
def test_example():
    # Arrange - Set up test data
    user_data = {'user_id': 1, 'name': 'Test'}
    
    # Act - Execute the function being tested
    result = validate_user(user_data)
    
    # Assert - Verify the result
    assert result['user_id'] == 1
    assert result['name'] == 'Test'
```

### 2. Test Independence
Each test should be independent:
```python
# ✅ Good - Test is self-contained
def test_user_creation():
    user = create_user({'name': 'John'})
    assert user.name == 'John'

# ❌ Bad - Test depends on previous test
def test_user_update():
    # Assumes user from previous test exists
    update_user(user.id, {'name': 'Jane'})
```

### 3. Clear Test Names
```python
# ✅ Good - Descriptive names
def test_import_csv_with_invalid_dates_raises_error()
def test_activity_model_converts_negative_steps_to_zero()

# ❌ Bad - Vague names  
def test_import()
def test_validation()
```

### 4. One Assertion Per Concept
```python
# ✅ Good - Testing one concept
def test_user_validation_with_valid_data():
    result = validate_user({'name': 'John', 'email': 'john@test.com'})
    assert result.is_valid == True

def test_user_validation_with_invalid_email():
    result = validate_user({'name': 'John', 'email': 'invalid'})
    assert result.is_valid == False
    assert 'email' in result.errors

# ⚠️ Acceptable - Related assertions
def test_activity_data_transformation():
    result = transform_activity({'steps': '8500', 'calories': '250'})
    assert result['steps'] == 8500      # Both test the same
    assert result['calories'] == 250.0  # transformation function
```

### 5. Use Descriptive Error Messages
```python
# ✅ Good - Helpful error message
assert len(results) == 3, f"Expected 3 results, got {len(results)}"

# ❌ Bad - Generic assertion
assert len(results) == 3
```

## Understanding Test Results

### Test Output Interpretation
```bash
tests/test_models.py::TestUserModel::test_validate_data_valid PASSED  [10%]
tests/test_models.py::TestUserModel::test_validate_invalid FAILED     [20%]
```

- **PASSED** ✅ - Test succeeded
- **FAILED** ❌ - Test failed (bug in code or test)
- **ERROR** ⚠️ - Test couldn't run (setup problem)
- **SKIPPED** ⏭️ - Test was skipped intentionally

### Test Coverage
Coverage shows which lines of code are tested:
```bash
pytest --cov=src --cov-report=html
```

**Coverage Guidelines**:
- **80%+ coverage** - Good for most projects
- **90%+ coverage** - Excellent for critical systems
- **100% coverage** - Usually overkill, diminishing returns

**Important**: High coverage doesn't guarantee good tests!

## Common Testing Patterns

### 1. Testing Exceptions
```python
def test_import_invalid_file_raises_error():
    with pytest.raises(ImportError, match="File not supported"):
        importer.import_file("invalid.txt")
```

### 2. Testing with Mock Data
```python
def test_database_connection_failure():
    with patch('sqlite3.connect') as mock_connect:
        mock_connect.side_effect = sqlite3.Error("Connection failed")
        
        with pytest.raises(sqlite3.Error):
            db = DatabaseConnection("test.db")
```

### 3. Parameterized Tests
```python
@pytest.mark.parametrize("input_val,expected", [
    ("5000", 5000),
    ("", 0),
    ("invalid", 0),
    (None, 0)
])
def test_safe_int_conversion(input_val, expected):
    result = safe_int_conversion(input_val)
    assert result == expected
```

### 4. Testing Time-Dependent Code
```python
def test_timestamp_creation():
    with patch('datetime.datetime') as mock_datetime:
        mock_datetime.now.return_value = datetime(2024, 1, 15, 12, 0, 0)
        
        result = create_timestamp()
        assert result == "2024-01-15 12:00:00"
```

## Test Maintenance

### When Tests Fail
1. **Read the error message** - Understanding what failed
2. **Check if it's a real bug** - Is the code wrong?
3. **Check if the test is wrong** - Did requirements change?
4. **Fix the root cause** - Don't just make tests pass

### Keeping Tests Maintainable
- **Keep tests simple** - Complex tests are hard to maintain
- **Use fixtures for common setup** - Reduce duplication
- **Update tests when requirements change** - Keep them relevant
- **Delete obsolete tests** - Remove tests for removed features

## Summary

### Testing Priority Order
1. **Unit Tests** (70% of your tests)
   - Fast, reliable, easy to write
   - Test business logic and validation
   - High ROI (Return on Investment)

2. **Integration Tests** (25% of your tests)
   - Test component interactions
   - Verify workflows work end-to-end
   - Medium ROI, higher confidence

3. **End-to-End Tests** (5% of your tests)
   - Test critical user journeys
   - Smoke tests for releases
   - Low ROI but highest confidence

### Key Takeaways
- **Start with unit tests** - They provide the most value
- **Test behavior, not implementation** - Focus on what, not how
- **Keep tests simple and readable** - Future you will thank you
- **Use meaningful test names** - Tests are documentation
- **Test the unhappy path** - Error conditions are important
- **Don't aim for 100% coverage** - Aim for testing important code

### For This Project
Our health data analytics system has:
- ✅ **69 unit tests** covering data models, validation, and transformations
- ✅ **Integration tests** for database operations and file imports  
- ✅ **Good test structure** with fixtures and clear organization
- ✅ **Proper categorization** with pytest markers

This provides a solid foundation for maintaining code quality and catching regressions during development.
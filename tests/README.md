# Testing Documentation

## Overview

This project includes a comprehensive testing suite organized into clear, focused test files that cover all aspects of the APIs project functionality.

## Test Structure

```
tests/
├── conftest.py                 # Global test configuration and fixtures
├── run_tests.py               # Main test runner script (executable)
├── test_fixtures.py           # Test data and mock utilities
├── test_comprehensive.py      # Comprehensive test suite
├── test_unit.py              # Unit tests for all service APIs
├── test_integration.py       # Integration tests between services
├── test_server.py            # Server tests for main API
└── README.md                 # This documentation
```

## Test Categories

### 1. Unit Tests (`test_unit.py`)

Tests individual service APIs in isolation with mocked dependencies:

**Spotify API Tests:**
- ✅ API initialization and configuration
- ✅ OAuth scopes validation
- ✅ Profile retrieval functionality
- ✅ Playback control methods

**Google API Tests:**
- ✅ API initialization and configuration
- ✅ OAuth scopes validation
- ✅ Service endpoint configuration

**Meta APIs Tests (Facebook & Instagram):**
- ✅ API initialization and configuration
- ✅ OAuth scopes validation
- ✅ Service-specific functionality

**WhatsApp API Tests:**
- ✅ API initialization and configuration
- ✅ Endpoint configuration validation
- ✅ Service-specific methods

**Files API Tests:**
- ✅ API initialization and configuration
- ✅ File operations (list, read, search)
- ✅ Error handling and validation

### 2. Integration Tests (`test_integration.py`)

Tests communication between services and server integration:

**Service Integration:**
- ✅ Spotify API integration with server
- ✅ Google API integration with server
- ✅ Facebook API integration with server
- ✅ Instagram API integration with server
- ✅ WhatsApp API integration with server
- ✅ Files API integration with server

**Server Integration:**
- ✅ Health endpoint functionality
- ✅ Services endpoint functionality
- ✅ Cross-service communication
- ✅ Error handling across services

### 3. Server Tests (`test_server.py`)

Tests main API server functionality and behavior:

**Server Endpoints:**
- ✅ Health endpoint testing
- ✅ Services endpoint testing
- ✅ All service-specific endpoints
- ✅ Response validation and status codes

**Authentication:**
- ✅ OAuth flow initiation for all services
- ✅ OAuth callback handling
- ✅ Unauthenticated access handling
- ✅ Session management

**Error Handling:**
- ✅ Invalid endpoint handling (404)
- ✅ Method not allowed handling (405)
- ✅ Missing parameter validation (400)
- ✅ Service unavailable scenarios (500/503)

**Performance:**
- ✅ Response time testing
- ✅ Concurrent request handling
- ✅ Memory usage monitoring

### 4. Comprehensive Tests (`test_comprehensive.py`)

End-to-end tests covering the complete system:

**Health and Server:**
- ✅ Health endpoint functionality
- ✅ Services endpoint functionality

**All Service Endpoints:**
- ✅ Spotify API endpoints (profile, playlists, playback)
- ✅ Google API endpoints (profile, Drive, Gmail)
- ✅ Facebook API endpoints (profile, pages, posts)
- ✅ Instagram API endpoints (profile, media, insights)
- ✅ WhatsApp API endpoints (status, chats, messaging)
- ✅ Files API endpoints (list, read, search)

**Authentication Flow:**
- ✅ OAuth flow initiation
- ✅ Callback handling
- ✅ Error scenarios

**Error Handling:**
- ✅ Invalid endpoints
- ✅ Method restrictions
- ✅ Parameter validation

**Performance:**
- ✅ Response time validation
- ✅ Concurrent request testing

## Running Tests

### Quick Start

```bash
# Run all tests
python tests/run_tests.py

# Run specific test types
python tests/run_tests.py --type unit
python tests/run_tests.py --type integration
python tests/run_tests.py --type server
python tests/run_tests.py --type comprehensive

# Run with coverage
python tests/run_tests.py --coverage

# Run with linting and type checking
python tests/run_tests.py --lint --type-check
```

### Using pytest directly

```bash
# Run all tests
pytest tests/

# Run specific test files
pytest tests/test_unit.py
pytest tests/test_integration.py
pytest tests/test_server.py
pytest tests/test_comprehensive.py

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Run specific test classes
pytest tests/test_unit.py::TestSpotifyAPI
pytest tests/test_server.py::TestServerEndpoints
```

### Test Markers

```bash
# Run tests by markers
pytest tests/ -m unit
pytest tests/ -m integration
pytest tests/ -m server
pytest tests/ -m performance
```

## Test Configuration

### conftest.py

Global test configuration including:
- Mock API responses for all services
- Test fixtures and utilities
- Common test helpers
- Mock authentication data

### test_fixtures.py

Test data and mock utilities:
- Mock credentials for all services
- Test file content and data
- Mock API responses
- Cleanup utilities

### pytest.ini

Pytest configuration with:
- Test discovery patterns
- Output formatting
- Markers for test categorization
- Coverage settings

## Mock Data

### API Responses

Comprehensive mock responses for all external APIs:
- **Spotify**: Profile, currently playing, playlists, playback control
- **Google**: Profile, Drive files, Gmail messages
- **Facebook**: Profile, pages, posts
- **Instagram**: Profile, media, insights
- **WhatsApp**: Status, chats, messages
- **Files**: File operations, search results

### Authentication

Mock credentials and tokens for all services to enable testing without real API calls.

## Continuous Integration

### GitHub Actions

Automated testing on:
- Multiple Python versions (3.9-3.12)
- Code linting and type checking
- Test coverage reporting
- Docker container testing

### Coverage

Coverage reporting includes:
- Line coverage
- Branch coverage
- HTML reports
- Codecov integration

## Test Utilities

### MockAPIResponse Class

Mock HTTP response objects for testing API calls with:
- Status code simulation
- JSON response data
- Error scenario testing

### TestFixtures Class

Utility methods for:
- Creating mock authentication files
- Generating test data
- Cleaning up test files
- Mock API responses

## Best Practices

### Test Organization

- One test file per test category
- Clear test class and method naming
- Descriptive test docstrings
- Proper use of fixtures and mocks

### Mocking Strategy

- Mock external API calls
- Mock file system operations
- Mock authentication flows
- Use dependency injection for testability

### Assertions

- Clear assertion messages
- Test both success and error cases
- Verify method calls and parameters
- Test edge cases and error conditions

## Debugging Tests

### Verbose Output

```bash
pytest tests/ -v -s
```

### Specific Test Debugging

```bash
pytest tests/test_unit.py::TestSpotifyAPI::test_initialization -v -s
pytest tests/test_server.py::TestServerEndpoints::test_health_endpoint -v -s
```

### Coverage Analysis

```bash
pytest tests/ --cov=. --cov-report=html
# Open htmlcov/index.html in browser
```

## Adding New Tests

### For New Service APIs

1. Add test class to `test_unit.py`
2. Follow existing test patterns
3. Add mock responses to `conftest.py`
4. Update test runner if needed

### For New Endpoints

1. Add tests to appropriate test file
2. Test success and error cases
3. Test authentication requirements
4. Test parameter validation

### For New Features

1. Add tests to `test_comprehensive.py` for end-to-end testing
2. Add specific tests to relevant category files
3. Update mock data as needed
4. Ensure proper error handling coverage

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure project root is in Python path
2. **Mock Failures**: Check mock setup and return values
3. **Authentication Errors**: Verify mock credentials
4. **File Not Found**: Check test fixture creation

### Test Environment

- Tests run in isolated environment
- Mock external dependencies
- Clean up after tests
- Use temporary directories for file operations

## Performance Testing

The test suite includes performance tests that verify:
- Response times under normal load
- Concurrent request handling
- Memory usage patterns
- Error recovery times

## Security Testing

Tests cover security aspects including:
- Authentication flow validation
- Token handling and refresh
- Input validation and sanitization
- Error message security (no sensitive data leakage)

This comprehensive testing structure ensures robust coverage of all functionality while maintaining clarity and ease of maintenance.
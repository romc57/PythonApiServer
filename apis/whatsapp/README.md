# WhatsApp API Documentation

## Overview
The WhatsApp API provides automated interaction with WhatsApp Web through Selenium WebDriver. It supports session persistence, automatic reconnection, message reading/sending, and chat discovery.

## Architecture Overview

```
WhatsApp API Structure
├── whatsapp_server_api.py     # Flask API endpoints
├── whatsapp_scraper.py        # Main orchestrator & unified functions
├── authentication.py          # Session management & auth detection
├── webdriver_manager.py       # Chrome WebDriver management
├── chat_discovery.py          # Chat list scanning & caching
├── message_reader.py          # Message extraction & sending
└── utils.py                   # Helper functions
```

## Core Components

### 1. WhatsApp Server API (`whatsapp_server_api.py`)
**Purpose**: Flask API endpoints that expose WhatsApp functionality to external clients.

**Key Methods**:
- `is_authenticated()` - Check if WhatsApp session is active
- `get_status()` - Get detailed authentication status
- `get_messages()` - Retrieve messages with flexible parameters
- `send_message()` - Send message to specific chat
- `get_latest_message()` - Get most recent message
- `get_qr_code()` - Get QR code for authentication

**Integration**: Uses `WhatsAppScraper` instance to handle all WhatsApp operations.

### 2. WhatsApp Scraper (`whatsapp_scraper.py`)
**Purpose**: Main orchestrator that coordinates all WhatsApp operations and provides unified scraping functions.

**Key Classes**:
- `WhatsAppScraper` - Main class that manages the entire WhatsApp session

**Key Methods**:
- `get_messages(limit, unread, chat, contact)` - **UNIFIED** message retrieval function
- `send_message(chat_name, message)` - Send message to specific chat
- `get_status()` - Get authentication status
- `_try_restore_session()` - Attempt to restore previous session
- `_update_chat_cache()` - Update chat name to DOM element mapping
- `_get_latest_messages_from_any_chat()` - Get messages from first available chat

**Performance Features**:
- **Chat ID Caching**: Maps chat names to DOM elements for faster access
- **Cache Updates**: Automatically updates cache when DOM changes
- **Rate Limiting**: Built-in delays to avoid detection

**Integration**: 
- Manages `AuthenticationManager`, `ChatDiscovery`, `MessageReader`
- Provides single source of truth for all WhatsApp operations

### 3. Authentication Manager (`authentication.py`)
**Purpose**: Handles WhatsApp Web authentication, session persistence, and connection status detection.

**Key Classes**:
- `AuthenticationManager` - Manages authentication state and session data

**Key Methods**:
- `check_authentication_status()` - **SINGLE SOURCE OF TRUTH** for auth status
- `get_status()` - Get detailed authentication information
- `_check_qr_code_present()` - Detect if QR code is visible
- `_check_chat_elements()` - Look for chat interface elements
- `_check_strong_auth_indicators()` - Check for other auth indicators
- `_update_session_data_on_auth()` - Save session data when authenticated
- `_update_session_data_on_auth_lost()` - Clear session data when disconnected

**Authentication Logic**:
1. **QR Code Present** → NOT connected (unless page is loading)
2. **Chat Elements Found** → IS connected
3. **Other Auth Indicators** → IS connected
4. **No Clear Indicators** → NOT connected

**Session Management**:
- Saves session data to `auth/whatsapp_personal_session.json`
- Tracks `authenticated`, `last_login`, `expired` status
- Enables automatic reconnection on container restart

### 4. WebDriver Manager (`webdriver_manager.py`)
**Purpose**: Manages Chrome WebDriver instance with proper profile handling and session persistence.

**Key Classes**:
- `WebDriverManager` - Handles WebDriver lifecycle and Chrome profile management

**Key Methods**:
- `get_driver()` - Get or create WebDriver instance
- `_get_user_data_dir()` - Create unique Chrome profile directory
- `_create_chrome_options()` - Configure Chrome options for WhatsApp Web
- `close()` - Clean up WebDriver resources

**Profile Management**:
- Creates unique Chrome profiles to avoid conflicts
- Copies existing profiles when restoring sessions
- Handles Chrome temporary files during profile copying
- Sets proper permissions for container access

### 5. Chat Discovery (`chat_discovery.py`)
**Purpose**: Discovers and caches chat list from WhatsApp Web sidebar.

**Key Classes**:
- `ChatDiscovery` - Scans and tracks available chats

**Key Methods**:
- `scan_chat_list()` - Scan sidebar for chat elements
- `_get_chat_elements()` - Find chat elements using CSS selectors
- `_extract_chat_name()` - Extract chat name from DOM element
- `_is_chat_element()` - Validate if element is a real chat item
- `_wait_for_chat_list_to_load()` - Wait for chat interface to load

**Chat Filtering**:
- Skips "Unknown" chats (failed name extraction)
- Skips "רם שולח לעצמו דברים" (hardcoded ignore)
- Maintains correct DOM order after filtering
- Updates cache with valid chats only

**Performance**:
- Caches chat elements to avoid repeated DOM queries
- Updates cache when new messages arrive
- Maintains chat name to DOM element mapping

### 6. Message Reader (`message_reader.py`)
**Purpose**: Extracts messages from specific chats and handles message sending.

**Key Classes**:
- `MessageReader` - Handles message operations

**Key Methods**:
- `read_messages_from_chat(dom_element, limit)` - Extract messages from chat
- `send_message_to_chat(message)` - Send message to currently open chat
- `_extract_message_info()` - Parse message data from DOM
- `_find_message_elements()` - Locate message elements using CSS selectors

**Message Extraction**:
- Uses comprehensive CSS selectors for different WhatsApp versions
- Extracts sender, text, timestamp, and read status
- Handles both incoming and outgoing messages
- Supports various message types (text, media, etc.)

### 7. Utils (`utils.py`)
**Purpose**: Helper functions used across WhatsApp components.

**Key Functions**:
- `log_with_timestamp()` - Consistent logging with timestamps
- `extract_text_safely()` - Safe text extraction from DOM elements
- `is_element_displayed()` - Check if element is visible
- `wait_for_element()` - Wait for element to appear

## Authentication & Session Management

### How Authentication Works

1. **Initial Connection**:
   - User starts WhatsApp session via API
   - System opens Chrome WebDriver with unique profile
   - Navigates to `https://web.whatsapp.com`
   - If no saved session, shows QR code for scanning

2. **QR Code Scanning**:
   - User scans QR code with WhatsApp mobile app
   - WhatsApp Web detects successful authentication
   - Session data is saved to `auth/whatsapp_personal_session.json`

3. **Session Persistence**:
   - Chrome profile directory contains all session cookies and data
   - Session file tracks authentication status and timestamps
   - Profile can be copied and reused for future sessions

### Automatic Reconnection on Container Restart

1. **Container Startup**:
   - `WhatsAppScraper` initializes and calls `_try_restore_session()`
   - `WebDriverManager` creates new Chrome profile or copies existing one
   - `AuthenticationManager` loads session data from JSON file

2. **Session Restoration Process**:
   - Loads existing Chrome profile with all cookies and session data
   - Navigates to WhatsApp Web
   - Waits up to 6 minutes (12 attempts × 30 seconds) for page to load
   - Calls `check_authentication_status()` to verify connection

3. **Authentication Verification**:
   - **Step 1**: Check if page is loading (minimal HTML content)
   - **Step 2**: Look for QR code (if present, NOT connected)
   - **Step 3**: Check for chat elements (if present, IS connected)
   - **Step 4**: Check other authentication indicators

4. **Success/Failure Handling**:
   - **Success**: Updates session data, starts background monitoring
   - **Failure**: Clears session data, requires new QR code scan

### Session Data Structure

```json
{
  "authenticated": true,
  "last_login": "2025-10-15T19:56:07.648686",
  "expired": null,
  "restore_error": null,
  "restore_failed": null,
  "restored": false
}
```

## API Endpoints

### Authentication
- `GET /whatsapp_personal/get_status` - Check authentication status
- `POST /whatsapp_personal/start_session` - Start new session
- `POST /whatsapp_personal/close_session` - Close current session
- `GET /whatsapp_personal/get_qr_code` - Get QR code for scanning

### Messages
- `GET /whatsapp_personal/get_messages` - Get messages with parameters
- `GET /whatsapp_personal/get_latest_message` - Get most recent message
- `GET /whatsapp_personal/get_messages_from_chat` - Get messages from specific chat
- `GET /whatsapp_personal/get_unread_messages` - Get unread messages only
- `POST /whatsapp_personal/send_message` - Send message to chat

## Data Flow

### Message Retrieval Flow
1. API endpoint receives request
2. `WhatsAppScraper.get_messages()` called with parameters
3. `AuthenticationManager.check_authentication_status()` verifies connection
4. `ChatDiscovery.scan_chat_list()` updates chat cache
5. `MessageReader.read_messages_from_chat()` extracts messages
6. Results formatted and returned to client

### Message Sending Flow
1. API endpoint receives send request
2. `WhatsAppScraper.send_message()` called with chat name and message
3. Authentication status checked
4. Chat cache updated to find target chat
5. Chat element clicked to open conversation
6. `MessageReader.send_message_to_chat()` types and sends message
7. Chat cache updated after sending

### Session Restoration Flow
1. Container starts and `WhatsAppScraper` initializes
2. `WebDriverManager` creates/copies Chrome profile
3. `AuthenticationManager` loads session data
4. Navigate to WhatsApp Web
5. Wait for page to load completely
6. `check_authentication_status()` determines connection state
7. Update session data based on result
8. Start background monitoring if connected

## Performance Optimizations

### Chat Caching
- **Cache Structure**: `{chat_name: {dom_element, last_updated, unread_count, order}}`
- **Update Triggers**: New messages, chat list changes, manual refresh
- **Benefits**: Faster chat lookup, reduced DOM queries

### Rate Limiting
- **Default Delay**: 1 second between operations
- **Configurable**: Can be adjusted via constructor parameter
- **Purpose**: Avoid detection and rate limiting by WhatsApp

### Lazy Loading
- **Chat Discovery**: Only scans when needed or after timeout
- **Message Reading**: Only reads messages when explicitly requested
- **Cache Updates**: Only updates when DOM changes detected

## Error Handling

### Authentication Errors
- **QR Code Present**: Clear session data, require new scan
- **Page Loading**: Wait and retry with exponential backoff
- **Network Issues**: Log error and retry connection
- **Session Expired**: Clear data and restart authentication

### Scraping Errors
- **Element Not Found**: Log warning and continue with next element
- **Timeout**: Retry with longer wait times
- **Invalid Data**: Skip invalid elements and continue processing
- **WebDriver Crashes**: Restart WebDriver and retry operation

## Configuration

### Environment Variables
- `HEADLESS`: Run Chrome in headless mode (default: false)
- `RATE_LIMIT_DELAY`: Delay between operations in seconds (default: 1.0)
- `MAX_RETRIES`: Maximum retry attempts (default: 3)

### File Paths
- Session Data: `auth/whatsapp_personal_session.json`
- Chrome Profiles: `auth/whatsapp/whatsapp_chrome_profile_*`
- Logs: Console output with timestamps

## Troubleshooting

### Common Issues

1. **"No chats found"**
   - Chat list not loaded yet - wait for `_wait_for_chat_list_to_load()`
   - Wrong CSS selectors - check WhatsApp Web HTML structure
   - Authentication failed - verify session status

2. **"Unknown" chats appearing**
   - Chat name extraction failing - check `_extract_chat_name()` selectors
   - Non-chat elements being processed - verify `_is_chat_element()` logic

3. **Session not restoring**
   - Chrome profile corrupted - delete and recreate
   - Session data invalid - clear and re-authenticate
   - Network issues - check internet connection

4. **Messages not found**
   - Wrong message selectors - update `message_selectors` in `MessageReader`
   - Chat not opened - ensure chat is clicked before reading messages
   - Rate limiting - increase delays between operations

### Debug Mode
Enable detailed logging by checking container logs:
```bash
docker logs api-server --tail 100 | grep -E "(WhatsApp|Chat|Message)"
```

## Security Considerations

- **Session Data**: Stored locally, not transmitted over network
- **Chrome Profiles**: Isolated per container instance
- **Rate Limiting**: Built-in delays to avoid detection
- **Error Handling**: Graceful degradation on failures
- **Cleanup**: Proper resource cleanup on shutdown

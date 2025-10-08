# 🚀 Clean API Server - Complete Documentation

A single Flask app with object-oriented API services. Maximum DRY principles with all common logic in the base class and only unique logic in inherited classes.

## 📑 Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Project Structure](#project-structure)
4. [Quick Start](#quick-start)
5. [API Services](#api-services)
   - [Spotify API](#spotify-api)
   - [Google API](#google-api)
   - [Facebook API](#facebook-api)
   - [Instagram API](#instagram-api)
   - [WhatsApp Personal API](#whatsapp-personal-api)
   - [SMS API](#sms-api)
6. [Authentication](#authentication)
7. [Setup Guides](#setup-guides)
   - [Meta APIs Setup](#meta-apis-setup)
   - [WhatsApp Personal Setup](#whatsapp-personal-setup)
8. [Troubleshooting](#troubleshooting)
   - [Instagram Issues](#instagram-issues)
   - [WhatsApp Issues](#whatsapp-issues)
9. [Testing](#testing)
10. [Security](#security)
11. [Adding New Services](#adding-new-services)
12. [Production Deployment](#production-deployment)

---

## 🎯 Overview

**Single Flask App**: One `app = Flask(__name__)` instance serving all APIs
**Object-Oriented**: Base class with all common functionality, inherited classes with only unique logic
**Clean Structure**: API type directories, consolidated requirements, single documentation

---

## 🏗️ Architecture

```
BaseAPI (Abstract Base Class)
├── All common functionality (OAuth, token management, requests, error handling)
├── Abstract methods: get_scopes(), get_endpoints(), get_service_info()
└── Concrete methods: authentication, token refresh, request handling

SpotifyAPI (Inherits BaseAPI)
├── Only Spotify-specific logic
├── Spotify endpoints and methods
└── Spotify credentials and scopes

GoogleAPI (Inherits BaseAPI)  
├── Only Google-specific logic
├── Google endpoints and methods
└── Google credentials and scopes

WhatsAppPersonalBaseAPI (Standalone)
├── Web scraping functionality
├── Session management
└── WhatsApp Web automation

APIServer (Single Flask App)
├── One Flask instance
├── Dynamic route setup
└── Service management
```

---

## 📁 Project Structure

```
apis/
├── api_server.py              # Single Flask app
├── base_api.py                # All common functionality
├── requirements.txt           # Consolidated dependencies
├── README.md                  # Complete documentation
├── docker-compose.yml        # Docker configuration
├── docker-compose.prod.yml   # Production Docker
├── Dockerfile                # Development image
├── Dockerfile.prod           # Production image
├── auth/                     # Authentication data
│   ├── spotify.json         # Spotify credentials
│   ├── google.json          # Google credentials
│   ├── facebook.json        # Facebook credentials
│   ├── instagram.json       # Instagram credentials
│   ├── whatsapp_personal.json # WhatsApp Personal config
│   └── sms.json             # SMS credentials
└── apis/                    # API type directories
    ├── spotify/             # Spotify-specific files
    ├── google/              # Google-specific files
    ├── meta/                # Meta (Facebook/Instagram) files
    ├── whatsapp/            # WhatsApp Personal files
    └── sms/                 # SMS files
```

---

## 🚀 Quick Start

```bash
# Start the clean API server
python api_server.py

# Or use Docker Compose
docker-compose up -d
```

---

## 📱 Access URLs

- **Dashboard**: http://localhost:8081
- **Health Check**: http://localhost:8081/health
- **Spotify Auth**: http://localhost:8081/spotify/auth
- **Google Auth**: http://localhost:8081/google/auth
- **Facebook Auth**: http://localhost:8081/facebook/auth
- **Instagram Auth**: http://localhost:8081/instagram/auth
- **WhatsApp Personal**: http://localhost:8081/whatsapp/auth
- **SMS**: http://localhost:8081/sms/send

---

## 🔧 API Services

### Spotify API

**Base URL:** `http://localhost:8081/spotify`

**Endpoints:**
- `GET /spotify/profile` - User profile
- `GET /spotify/playlists` - User playlists
- `GET /spotify/currently-playing` - Currently playing track
- `GET /spotify/search?q=query` - Search music
- `POST /spotify/playback/next` - Skip to next track
- `POST /spotify/playback/pause` - Pause playback
- `POST /spotify/playback/resume` - Resume playback

**Authentication:** OAuth 2.0
**Scopes:** `user-read-private`, `user-read-email`, `playlist-read-private`, `user-read-currently-playing`, `user-modify-playback-state`

### Google API

**Base URL:** `http://localhost:8081/google`

**Endpoints:**
- `GET /google/gmail/profile` - Gmail profile
- `GET /google/gmail/messages` - List messages
- `GET /google/drive/files` - List Drive files
- `GET /google/calendar/events` - List events
- `GET /google/youtube/search?q=query` - Search videos
- `GET /google/photos/list` - List photos
- `GET /google/places/search?q=query` - Search places

**Authentication:** OAuth 2.0
**Scopes:** `https://www.googleapis.com/auth/gmail.readonly`, `https://www.googleapis.com/auth/drive.readonly`, `https://www.googleapis.com/auth/calendar.readonly`, `https://www.googleapis.com/auth/youtube.readonly`, `https://www.googleapis.com/auth/photoslibrary.readonly`, `https://www.googleapis.com/auth/places.readonly`

### Facebook API

**Base URL:** `http://localhost:8081/facebook`

**Endpoints:**
- `GET /facebook/profile` - Get user profile
- `GET /facebook/posts` - Get user's posts
- `GET /facebook/photos` - Get user's photos
- `GET /facebook/pages` - Get user's pages
- `POST /facebook/create-post` - Create a post

**Authentication:** OAuth 2.0
**Scopes:** `public_profile`, `email`, `user_posts`, `user_photos`, `pages_manage_posts`

### Instagram API

**Base URL:** `http://localhost:8081/instagram`

**Endpoints:**
- `GET /instagram/profile` - Get user profile
- `GET /instagram/media` - Get user's media
- `GET /instagram/media-details` - Get media details
- `POST /instagram/long-lived-token` - Get long-lived token

**Authentication:** OAuth 2.0
**Scopes:** `user_profile`, `user_media`

### WhatsApp Personal API

**Base URL:** `http://localhost:8081/whatsapp_personal`

**Endpoints:**
- `POST /whatsapp_personal/start-session` - Start WhatsApp Web session
- `POST /whatsapp_personal/close-session` - Close session
- `GET /whatsapp_personal/contacts?limit=50` - Get contacts
- `GET /whatsapp_personal/conversations?limit=20` - Get conversations
- `GET /whatsapp_personal/search?query=name` - Search conversations
- `GET /whatsapp_personal/messages?limit=50` - Get messages from current chat
- `POST /whatsapp_personal/send-message` - Send message to contact
- `GET /whatsapp_personal/status` - Get API status

**Authentication:** QR Code (Web Scraping)
**Features:** Web scraping, session management, rate limiting

### SMS API

**Base URL:** `http://localhost:8081/sms`

**Endpoints:**
- `POST /sms/send` - Send SMS message

**Authentication:** API Key
**Features:** SMS sending via external service

---

## 🔐 Authentication

### OAuth 2.0 Services (Spotify, Google, Facebook, Instagram)
1. Visit `/service/auth` → Complete OAuth → Access service endpoints
2. Tokens are automatically managed and refreshed
3. Session data stored in `auth/` directory

### WhatsApp Personal API
1. Visit `/whatsapp/auth` → Start session → Scan QR code → Access WhatsApp endpoints
2. Session data stored in `auth/whatsapp_personal_session.json`
3. Requires Chrome browser and display

### SMS API
1. Configure API key in `auth/sms.json`
2. Direct API access without OAuth

---

## 📋 Setup Guides

### Meta APIs Setup

#### Prerequisites
1. **Facebook Business Account** (Free)
2. **Facebook Developer Account** (Free)

#### Step 1: Create Facebook App
1. Go to [Facebook Developers](https://developers.facebook.com/)
2. Click "Create App"
3. Choose "Business" as app type
4. Fill in app details

#### Step 2: Configure Facebook App
1. Add Products:
   - **Facebook Login** (for Facebook API)
   - **Instagram Basic Display** (for Instagram API)

2. Configure Facebook Login:
   - Add Valid OAuth Redirect URIs:
     - `http://localhost:8081/facebook/callback`
     - `http://localhost:8081/instagram/callback`

3. Configure Instagram Basic Display:
   - Add Instagram Testers (your Instagram account)
   - Add Valid OAuth Redirect URIs:
     - `http://localhost:8081/instagram/callback`

#### Step 3: Get Credentials
From your Facebook App dashboard, get:
- **App ID** (from App Settings)
- **App Secret** (from App Settings)

#### Step 4: Configure Your Project

**auth/facebook.json:**
```json
{
  "app_id": "YOUR_FACEBOOK_APP_ID",
  "app_secret": "YOUR_FACEBOOK_APP_SECRET",
  "redirect_uri": "http://localhost:8081/facebook/callback"
}
```

**auth/instagram.json:**
```json
{
  "app_id": "YOUR_FACEBOOK_APP_ID",
  "app_secret": "YOUR_FACEBOOK_APP_SECRET",
  "redirect_uri": "http://localhost:8081/instagram/callback"
}
```

### WhatsApp Personal Setup

#### Prerequisites
- Chrome browser installed
- Stable internet connection
- WhatsApp Web accessible

#### Configuration
Create `auth/whatsapp_personal.json`:
```json
{
  "session_data_path": "auth/whatsapp_personal_session.json",
  "headless": false,
  "rate_limit_delay": 1.0,
  "max_retries": 3,
  "max_contacts": 100,
  "max_conversations": 50,
  "max_messages": 100,
  "chrome_options": {
    "window_size": "1920,1080",
    "disable_images": true,
    "disable_notifications": true
  }
}
```

#### Usage
1. Start session: `POST /whatsapp_personal/start-session`
2. Scan QR code with your phone
3. Use other endpoints once authenticated

---

## 🚨 Troubleshooting

### Instagram Issues

#### Common Error: "There is an error in logging you into this application"

**Most Common Cause:** Instagram Testers Not Added

**Solution:**
1. Go to Facebook Developers → Your App → Instagram Basic Display → Basic Display
2. Click "Add or Remove Instagram Testers"
3. Add your Instagram username
4. Check your Instagram app for invitation
5. Accept the invitation
6. Wait 5-10 minutes for changes to take effect

#### Other Common Issues:

1. **Redirect URI Mismatch**
   - Check Facebook App Settings
   - Verify exact match: `http://localhost:8081/instagram/callback`
   - No trailing slash, correct protocol and port

2. **App Not Properly Configured**
   - Enable Instagram Basic Display
   - Configure Basic Display settings
   - Check App Mode (Development vs Live)

3. **Instagram Account Issues**
   - Connect Instagram to Facebook
   - Check account status and restrictions
   - Ensure account is active

4. **Credentials Not Updated**
   - Get correct App ID and App Secret
   - Update `auth/instagram.json` with real values
   - Restart server after updating

### WhatsApp Issues

#### Chrome WebDriver Error in Docker

**Error:** `'NoneType' object has no attribute 'split'`

**Cause:** Docker has no display for browser windows

**Solutions:**
1. **Run Locally (Recommended):**
   ```bash
   docker compose down
   python api_server.py
   ```

2. **Use Headless Mode (Limited):**
   - Set `"headless": true` in config
   - Limited functionality in headless mode

#### Common WhatsApp Issues:

1. **Authentication Issues:**
   - Scan QR code within 30 seconds
   - Ensure WhatsApp Web is accessible
   - Check for browser popup blockers

2. **Element Not Found:**
   - Wait for page to fully load
   - Check if WhatsApp Web interface has changed
   - Try refreshing the session

3. **Rate Limiting:**
   - Increase `rate_limit_delay` in config
   - Reduce limits for data retrieval
   - Wait between operations

---

## 🧪 Testing

```bash
# Test specific endpoints
curl http://localhost:8081/health
curl http://localhost:8081/spotify/profile
curl http://localhost:8081/google/gmail/profile
curl http://localhost:8081/facebook/profile
curl http://localhost:8081/instagram/profile
curl http://localhost:8081/whatsapp_personal/status
```

---

## 🔒 Security

- **OAuth 2.0**: Secure authentication flow for most services
- **Token Management**: Automatic refresh and persistence
- **Non-root User**: Production containers run as non-root
- **Resource Limits**: Memory limits in production
- **Health Checks**: Container health monitoring
- **Rate Limiting**: Built-in protection against abuse
- **Session Management**: Proper cleanup and security

---

## 🛠️ Adding New Services

To add a new API service:

1. **Create API Directory**: `mkdir apis/twitter`
2. **Create API Class**:
```python
class TwitterAPI(BaseAPI):
    def __init__(self):
        super().__init__(
            service_name='twitter',
            client_id=...,
            client_secret=...,
            redirect_uri=...,
            auth_url='https://api.twitter.com/oauth/authorize',
            token_url='https://api.twitter.com/oauth2/token',
            api_base_url='https://api.twitter.com/2'
        )
    
    def get_scopes(self) -> List[str]:
        return ['tweet.read', 'users.read']
    
    def get_endpoints(self) -> Dict[str, Dict[str, Any]]:
        return {
            "tweets": {
                "method": "GET",
                "description": "Get user tweets",
                "handler": self.get_tweets
            }
        }
    
    def get_service_info(self) -> Dict[str, Any]:
        return {
            "name": "Twitter",
            "description": "Social media API",
            "icon": "🐦",
            "color": "#1da1f2"
        }
    
    def get_tweets(self) -> Dict[str, Any]:
        response = self._make_request('GET', '/tweets')
        return response.json()
```

3. **Register Service**: Add to `services` dict in `api_server.py`
4. **Add Credentials**: Create `auth/twitter.json`

The server automatically creates all routes, handles authentication, and updates the dashboard!

---

## 🏛️ Code Structure

### BaseAPI Class (All Common Logic)
```python
class BaseAPI(ABC):
    """Base class with ALL common functionality."""
    
    def __init__(self, service_name, client_id, client_secret, ...):
        # Common initialization for all services
    
    def get_auth_url(self) -> str:
        # Common OAuth URL generation
    
    def handle_callback(self, code: str) -> bool:
        # Common callback handling
    
    def _refresh_token(self) -> bool:
        # Common token refresh logic
    
    def _make_request(self, method: str, endpoint: str, **kwargs):
        # Common request handling with retry logic
    
    @abstractmethod
    def get_scopes(self) -> List[str]:
        # Service-specific scopes
    
    @abstractmethod
    def get_endpoints(self) -> Dict[str, Dict[str, Any]]:
        # Service-specific endpoints
    
    @abstractmethod
    def get_service_info(self) -> Dict[str, Any]:
        # Service-specific info
```

### Inherited Classes (Only Unique Logic)
```python
class SpotifyAPI(BaseAPI):
    """Only Spotify-specific logic."""
    
    def get_scopes(self) -> List[str]:
        return ['user-read-private', 'user-read-email', ...]
    
    def get_profile(self) -> Dict[str, Any]:
        response = self._make_request('GET', '/me')
        return response.json()
```

### Single Flask App
```python
app = Flask(__name__)  # Only one Flask instance

services = {
    'spotify': SpotifyAPI(),
    'google': GoogleAPI(),
    'facebook': FacebookAPI(),
    'instagram': InstagramAPI(),
    'whatsapp_personal': WhatsAppPersonalBaseAPI(),
    'sms': SMSAPI()
}

# Dynamic route setup for all services
for service_name, service in services.items():
    # Setup auth routes
    # Setup API routes
    # Setup documentation routes
```

---

## 📊 Benefits

- **Single Flask App**: No duplicate Flask instances
- **Maximum DRY**: All common logic inherited
- **Clean Structure**: Organized by API type
- **Consolidated Dependencies**: Single requirements file
- **Single Documentation**: One comprehensive guide
- **Easy Extension**: Add new services by inheriting BaseAPI
- **Maintainable**: Clear separation of concerns
- **Scalable**: Easy to add new services
- **Secure**: Built-in security features
- **Testable**: Comprehensive testing framework

---

## 🚀 Production Deployment

### Docker Production Setup
```bash
# Build production image
docker-compose -f docker-compose.prod.yml build

# Run production
docker-compose -f docker-compose.prod.yml up -d
```

### Environment Variables
For production, use environment variables for:
- Database credentials
- API keys and secrets
- Redirect URIs
- Webhook URLs

### Security Considerations
1. **Use HTTPS** in production
2. **Rotate API secrets** regularly
3. **Set up monitoring** and logging
4. **Use proper firewall** rules
5. **Regular security updates**

---

## 📄 License

MIT License

---

## 📞 Support

For issues or questions:
1. Check the troubleshooting section
2. Review error messages in API responses
3. Check server logs
4. Verify credentials and configuration
5. Test with provided examples

---

**Remember:** This API server is designed for personal and business use. Always respect the Terms of Service of each service and use responsibly.
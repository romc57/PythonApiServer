"""Single Flask app with all API services."""
from flask import Flask, request, jsonify, redirect, render_template_string
from typing import Dict, Any
from base_api import BaseAPI
from apis.spotify.spotify_api import SpotifyAPI
from apis.google.google_api import GoogleAPI
from apis.whatsapp.whatsapp_personal_base import WhatsAppPersonalBaseAPI
from apis.meta.facebook_api import FacebookAPI
from apis.meta.instagram_api import InstagramAPI
from apis.files.files_base_api import FilesBaseAPI
import json

# Single Flask app instance
app = Flask(__name__)

# Load Meta API credentials
def load_meta_credentials():
    """Load Meta API credentials for Facebook and Instagram."""
    services = {}
    
    try:
        # Load Facebook credentials (required for all Meta APIs)
        with open('auth/facebook.json', 'r') as f:
            facebook_creds = json.load(f)
        
        app_id = facebook_creds['app_id']
        app_secret = facebook_creds['app_secret']
        
        # Add Facebook API
        services['facebook'] = FacebookAPI(app_id, app_secret)
        
        # Add Instagram API (uses same credentials)
        services['instagram'] = InstagramAPI(app_id, app_secret)
            
    except FileNotFoundError as e:
        print(f"Warning: Facebook API credentials not found: {e}")
        print("   Please configure auth/facebook.json to use Meta APIs")
    
    return services

# Initialize all services
meta_services = load_meta_credentials()

# Initialize personal WhatsApp API
whatsapp_personal = WhatsAppPersonalBaseAPI()

# Initialize Files API
files_api = FilesBaseAPI()

services: Dict[str, Any] = {
    'spotify': SpotifyAPI(),
    'google': GoogleAPI(),
    'whatsapp_personal': whatsapp_personal,
    'files': files_api,
    **meta_services
}

def setup_routes():
    """Setup all routes dynamically."""
    
    @app.route('/')
    def dashboard():
        """Main dashboard showing all services."""
        return render_dashboard()
    
    @app.route('/whatsapp/auth')
    def whatsapp_auth():
        """WhatsApp auth endpoint - shows start session form directly."""
        if 'whatsapp_personal' in services:
            return services['whatsapp_personal'].start_session_form()
        else:
            return "WhatsApp Personal API not available", 503
    
    @app.route('/health')
    def health():
        """Health check endpoint."""
        return jsonify(get_health_status())
    
    @app.route('/test-token-exchange')
    def test_token_exchange():
        """Test token exchange manually."""
        try:
            # Use the same code that worked in our manual test
            test_code = "AQDO5H50htPkCMNn4K2vYpLmcQ8PcJ95UJu8zXVOsKs-g-SyNL8XBSmKybEva7gZmBWM9XIDuwkFMg1SKgVvU-kMbDJLbi8mkeWhRQ1NpJETHu5AQUlBonNZpPaEFPaE3lzxGI2p_MD4AJvC9JrodhhTmv5C0xQKnJQMP7nJxVFuKwhZk_SVBsLiTe3BlChQyZbCdHuVOpODB5qS7T0cJtPJDh7jn_70_P58UfYQ7lP1OJTAmpBA2QtmjdwyKSM-XE86rihvuvy371bS2eIqgI-XzER1lYwGwIsQYHO5davjopCCimtSgrk_VfASYVmbT3XllE-CSt2mcHcettu-uueeVzyN8sHyONEw4soeP9XgMrKwKFbigb23OH_Q9tjyFzCFofolWpUBQzalv4AhW0IDdBWAQDsEC_tNtSX0Etzjr6BMYmhyTmVYWD1xG5VsB2u1Ax-_pWl4rb8N-85mwtqt6gNuGj6Wq9agtHqgaEAbVw"
            
            print(f"Testing token exchange with code: {test_code[:20]}...")
            result = services['spotify'].handle_callback(test_code)
            print(f"Token exchange result: {result}")
            
            return jsonify({
                "success": result,
                "message": "Token exchange test completed",
                "authenticated": services['spotify'].is_authenticated()
            })
        except Exception as e:
            print(f"Error in test token exchange: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return jsonify({"error": str(e)}), 500
    
    
    # Setup routes for each service
    for service_name, service in services.items():
        setup_service_routes(service_name, service)

def create_api_route_handler(handler, service, service_name: str):
    """Create a generic API route handler with common authentication logic."""
    def route_handler():
        """Generic API route handler."""
        # Special handling for WhatsApp Personal API
        if service_name == 'whatsapp_personal':
            result = handler()
            # Check if result is a string (HTML) or dict (JSON)
            if isinstance(result, str):
                return result, 200
            else:
                status_code = 200 if 'error' not in result else 500
                return jsonify(result), status_code
        
        # Special handling for Files API (no OAuth required)
        if service_name == 'files':
            # Extract query parameters for Files API
            if hasattr(handler, '__name__'):
                if 'read' in handler.__name__:
                    filename = request.args.get('filename')
                    if not filename:
                        return jsonify({"success": False, "error": "filename parameter required"}), 400
                    result = handler(filename)
                elif 'search' in handler.__name__:
                    query = request.args.get('query')
                    if not query:
                        return jsonify({"success": False, "error": "query parameter required"}), 400
                    result = handler(query)
                elif 'list' in handler.__name__:
                    extension = request.args.get('extension')
                    result = handler(extension)
                elif 'create' in handler.__name__ or 'update' in handler.__name__:
                    data = request.get_json()
                    if not data:
                        return jsonify({"success": False, "error": "JSON data required"}), 400
                    filename = data.get('filename')
                    content = data.get('content')
                    if not filename or content is None:
                        return jsonify({"success": False, "error": "filename and content required"}), 400
                    result = handler(filename, content)
                elif 'delete' in handler.__name__:
                    filename = request.args.get('filename')
                    if not filename:
                        return jsonify({"success": False, "error": "filename parameter required"}), 400
                    result = handler(filename)
                else:
                    result = handler()
            else:
                result = handler()
            status_code = 200 if 'error' not in result else 500
            return jsonify(result), status_code
        
        # Standard OAuth API handling
        if not service.is_authenticated():
            return jsonify({"error": f"{service_name.title()} authentication required"}), 401
        
        result = handler()
        status_code = 200 if 'error' not in result else 500
        return jsonify(result), status_code
    
    return route_handler

def setup_service_routes(service_name: str, service):
    """Setup routes for a specific service."""
    
    # Special handling for WhatsApp Personal API (no OAuth)
    if service_name == 'whatsapp_personal':
        # No auth/callback routes needed for WhatsApp Personal API
        pass
    
    # Special handling for Files API (no OAuth)
    elif service_name == 'files':
        # No auth/callback routes needed for Files API
        pass
    else:
        # Auth route for OAuth-based APIs
        def auth_handler():
            """Start OAuth flow for service."""
            auth_url = service.get_auth_url()
            return redirect(auth_url)
        auth_handler.__name__ = f"{service_name}_auth_route"
        app.add_url_rule(f'/{service_name}/auth', f"{service_name}_auth_route", auth_handler)
        
        # Callback route for OAuth-based APIs
        def callback_handler():
            """Handle OAuth callback for service."""
            print(f"=== CALLBACK HANDLER CALLED FOR {service_name.upper()} ===")
            print(f"Request args: {dict(request.args)}")
            code = request.args.get('code')
            error = request.args.get('error')
            
            print(f"Code: {code[:20] if code else 'None'}...")
            print(f"Error: {error}")
            
            if error:
                print(f"OAuth error detected: {error}")
                return f"{service_name.title()} OAuth error: {error}", 400
            
            if not code:
                print("No authorization code received")
                return "No authorization code received", 400
            
            try:
                print(f"Attempting to handle callback for {service_name} with code: {code[:20]}...")
                print(f"About to call service.handle_callback()...")
                result = service.handle_callback(code)
                print(f"handle_callback result: {result}")
                print(f"Result type: {type(result)}")
                if result:
                    print(f"✅ Token exchange successful, redirecting to dashboard")
                    return redirect('/')
                else:
                    print(f"❌ {service_name.title()} handle_callback returned False for code: {code[:20]}...")
                    return "Failed to exchange code for tokens", 400
            except Exception as e:
                print(f"Exception in {service_name} callback handler: {e}")
                print(f"Exception type: {type(e)}")
                import traceback
                print(f"Traceback: {traceback.format_exc()}")
                return f"Callback error: {str(e)}", 400
        callback_handler.__name__ = f"{service_name}_callback_route"
        app.add_url_rule(f'/{service_name}/callback', f"{service_name}_callback_route", callback_handler)
    
    # Setup API endpoints for this service
    endpoints = service.get_endpoints()
    for endpoint_path, endpoint_config in endpoints.items():
        method = endpoint_config['method'].lower()
        handler = endpoint_config['handler']
        
        route_path = f'/{service_name}/{endpoint_path}'
        
        # Create unique function name for each route
        func_name = f"{service_name}_{endpoint_path.replace('/', '_')}_{method}"
        
        # Create the route handler function dynamically
        def make_route_handler(h=handler, s=service, sn=service_name):
            def route_handler():
                return create_api_route_handler(h, s, sn)()
            route_handler.__name__ = func_name
            return route_handler
        
        if method == 'get':
            app.add_url_rule(route_path, func_name, make_route_handler(), methods=['GET'])
        elif method == 'post':
            app.add_url_rule(route_path, func_name, make_route_handler(), methods=['POST'])
        elif method == 'put':
            app.add_url_rule(route_path, func_name, make_route_handler(), methods=['PUT'])
        elif method == 'delete':
            app.add_url_rule(route_path, func_name, make_route_handler(), methods=['DELETE'])
    
    # Documentation route
    def docs_handler():
        """Service-specific documentation."""
        service_info = service.get_service_info()
        endpoints = service.get_endpoints()
        return render_service_docs(service_info, endpoints, service_name)
    docs_handler.__name__ = f"{service_name}_service_docs"
    app.add_url_rule(f'/docs/{service_name}', f"{service_name}_service_docs", docs_handler)

def render_dashboard() -> str:
    """Render the main dashboard."""
    template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>API Server Dashboard</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 1200px; margin: 50px auto; padding: 20px; }
            .container { background: #f8f9fa; padding: 30px; border-radius: 10px; }
            .service { background: white; margin: 20px 0; padding: 25px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .button { background: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 8px 5px; }
            .button:hover { background: #0056b3; }
            .status { padding: 8px 16px; border-radius: 20px; font-size: 14px; font-weight: bold; }
            .authenticated { background: #d4edda; color: #155724; }
            .not-authenticated { background: #f8d7da; color: #721c24; }
            .endpoints { margin-top: 20px; }
            .endpoint { background: #f8f9fa; padding: 10px; margin: 8px 0; border-radius: 4px; font-family: monospace; font-size: 13px; border-left: 3px solid #dee2e6; }
            .method { font-weight: bold; }
            .get { color: #28a745; }
            .post { color: #fd7e14; }
            h1 { color: #343a40; text-align: center; }
            h2 { color: #495057; margin-top: 25px; }
            .header { text-align: center; margin-bottom: 30px; }
            .service-icon { font-size: 2em; margin-right: 10px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚀 API Server Dashboard</h1>
                <p>Single Flask app with object-oriented API services</p>
            </div>
            
            {% for service_name, service in services.items() %}
            <div class="service" style="border-left: 4px solid {{ service.get_service_info().color }};">
                <h2><span class="service-icon">{{ service.get_service_info().icon }}</span>{{ service.get_service_info().name }} API</h2>
                <p>{{ service.get_service_info().description }}</p>
                <p>Status: <span class="status {{ 'authenticated' if service.is_authenticated() else 'not-authenticated' }}">
                    {{ 'Authenticated' if service.is_authenticated() else 'Not Authenticated' }}
                </span></p>
                
                {% if service.is_authenticated() %}
                    <p>✅ Ready to use - All {{ service.get_service_info().name }} endpoints available</p>
                {% else %}
                    {% if service_name == 'whatsapp_personal' %}
                        <a href="/whatsapp_personal/start-session-form" class="button" style="background: {{ service.get_service_info().color }};">🔐 Start {{ service.get_service_info().name }} Session</a>
                    {% elif service_name == 'files' %}
                        <a href="/files/list" class="button" style="background: {{ service.get_service_info().color }};">📁 Browse {{ service.get_service_info().name }}</a>
                    {% else %}
                        <a href="{{ service.get_service_info().auth_url }}" class="button" style="background: {{ service.get_service_info().color }};">🔐 Authenticate {{ service.get_service_info().name }}</a>
                    {% endif %}
                {% endif %}
                
                <div class="endpoints">
                    <h3>📋 Available Endpoints:</h3>
                    {% for endpoint_path, endpoint_config in service.get_endpoints().items() %}
                    <div class="endpoint">
                        <span class="method {{ endpoint_config.method.lower() }}">{{ endpoint_config.method }}</span> 
                        /{{ service_name }}/{{ endpoint_path }} - {{ endpoint_config.description }}
                    </div>
                    {% endfor %}
                </div>
            </div>
            {% endfor %}
            
            <div style="margin-top: 40px; padding: 25px; background: #e9ecef; border-radius: 8px; text-align: center;">
                <h3>📚 Quick Links</h3>
                {% for service_name, service in services.items() %}
                <a href="/docs/{{ service_name }}" class="button">📖 {{ service.get_service_info().name }} Documentation</a>
                {% endfor %}
                <a href="/health" class="button">🏥 Health Check</a>
            </div>
        </div>
    </body>
    </html>
    """
    
    return render_template_string(template, services=services)

def render_service_docs(service_info: Dict[str, Any], endpoints: Dict[str, Dict[str, Any]], service_name: str) -> str:
    """Render service-specific documentation."""
    template = f"""
    <h1>{service_info['icon']} {service_info['name']} API Documentation</h1>
    <h2>Authentication</h2>
    <p>Visit <a href="{service_info['auth_url']}">{service_info['auth_url']}</a> to authenticate</p>
    
    <h2>Endpoints</h2>
    <ul>
    """
    
    for endpoint_path, endpoint_config in endpoints.items():
        template += f"""
        <li><strong>{endpoint_config['method']} /{service_name}/{endpoint_path}</strong> - {endpoint_config['description']}</li>
        """
    
    template += """
    </ul>
    
    <p><a href="/">← Back to dashboard</a></p>
    """
    
    return template

def get_health_status() -> Dict[str, Any]:
    """Get overall health status."""
    service_statuses = {}
    overall_healthy = True
    
    for service_name, service in services.items():
        status = service.get_status()
        service_statuses[service_name] = status
        if not status['authenticated']:
            overall_healthy = False
    
    return {
        "status": "healthy" if overall_healthy else "degraded",
        "services": service_statuses,
        "total_services": len(services),
        "authenticated_services": sum(1 for s in service_statuses.values() if s['authenticated'])
    }

# Setup all routes
setup_routes()

if __name__ == '__main__':
    print("🚀 Starting Single Flask API Server...")
    print("📊 Dashboard: http://127.0.0.1:8081")
    print("🏥 Health: http://127.0.0.1:8081/health")
    for service_name, service in services.items():
        service_info = service.get_service_info()
        print(f"{service_info['icon']} {service_info['name']}: http://127.0.0.1:8081/{service_name}/")
    print("Press Ctrl+C to stop the server")
    
    app.run(host='0.0.0.0', port=8081, debug=True)
"""
Files Base API - Integration with the main API server
"""

from typing import Dict, List, Any
from .files_api import FilesAPI


class FilesBaseAPI:
    """Base API class for Files service integration."""
    
    def __init__(self):
        self.service_name = 'files'
        self.files_api = FilesAPI()
    
    def get_scopes(self) -> List[str]:
        """Get required scopes for the Files API."""
        return []  # No OAuth required for local file operations
    
    def get_endpoints(self) -> Dict[str, Dict[str, Any]]:
        """Get available endpoints for the Files API."""
        return {
            "list": {
                "method": "GET",
                "description": "List all files in local-data directory",
                "handler": self.list_files,
                "parameters": {
                    "extension": "Optional file extension filter (e.g., '.txt')"
                }
            },
            "read": {
                "method": "GET", 
                "description": "Read content of a specific file",
                "handler": self.read_file,
                "parameters": {
                    "filename": "Name of the file to read"
                }
            },
            "create": {
                "method": "POST",
                "description": "Create a new file with content",
                "handler": self.create_file,
                "parameters": {
                    "filename": "Name of the file to create",
                    "content": "Content to write to the file"
                }
            },
            "update": {
                "method": "PUT",
                "description": "Update content of an existing file",
                "handler": self.update_file,
                "parameters": {
                    "filename": "Name of the file to update",
                    "content": "New content for the file"
                }
            },
            "delete": {
                "method": "DELETE",
                "description": "Delete a file",
                "handler": self.delete_file,
                "parameters": {
                    "filename": "Name of the file to delete"
                }
            },
            "search": {
                "method": "GET",
                "description": "Search for files containing specific text",
                "handler": self.search_files,
                "parameters": {
                    "query": "Text to search for in files"
                }
            },
            "stats": {
                "method": "GET",
                "description": "Get file statistics for the directory",
                "handler": self.get_file_stats
            }
        }
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get service information."""
        return {
            "name": "Files",
            "description": "CRUD operations on local files in local-data directory",
            "icon": "📁",
            "color": "#4CAF50",
            "auth_url": "/files/list",
            "callback_url": "/files/list"
        }
    
    def is_authenticated(self) -> bool:
        """Check if the service is authenticated."""
        return True  # No authentication required for local file operations
    
    def get_auth_url(self) -> str:
        """Get authentication URL."""
        return "/files/list"  # Redirect to file listing
    
    def handle_callback(self, code: str) -> bool:
        """Handle OAuth callback."""
        return True  # No OAuth required
    
    def get_access_token(self) -> str:
        """Get access token."""
        return "local_access"  # No token required
    
    # API endpoint handlers
    def list_files(self, extension: str = None) -> Dict[str, Any]:
        """List files endpoint."""
        return self.files_api.list_files(extension)
    
    def read_file(self, filename: str) -> Dict[str, Any]:
        """Read file endpoint."""
        return self.files_api.read_file(filename)
    
    def create_file(self, filename: str, content: str) -> Dict[str, Any]:
        """Create file endpoint."""
        return self.files_api.create_file(filename, content)
    
    def update_file(self, filename: str, content: str) -> Dict[str, Any]:
        """Update file endpoint."""
        return self.files_api.update_file(filename, content)
    
    def delete_file(self, filename: str) -> Dict[str, Any]:
        """Delete file endpoint."""
        return self.files_api.delete_file(filename)
    
    def search_files(self, query: str) -> Dict[str, Any]:
        """Search files endpoint."""
        return self.files_api.search_files(query)
    
    def get_file_stats(self) -> Dict[str, Any]:
        """Get file stats endpoint."""
        return self.files_api.get_file_stats()

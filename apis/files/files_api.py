"""
Files API - CRUD operations on local files
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime


class FilesAPI:
    """API for CRUD operations on local files in the local-data directory."""
    
    def __init__(self, base_path: str = "local-data"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
        
    def _get_file_path(self, filename: str) -> Path:
        """Get the full path for a file, ensuring it's within the base directory."""
        # Prevent directory traversal attacks
        safe_filename = os.path.basename(filename)
        return self.base_path / safe_filename
    
    def _is_safe_filename(self, filename: str) -> bool:
        """Check if filename is safe (no directory traversal)."""
        safe_filename = os.path.basename(filename)
        return safe_filename == filename and len(filename) > 0
    
    def _get_file_info(self, file_path: Path) -> Dict[str, Any]:
        """Get file information."""
        if not file_path.exists():
            return {}
            
        stat = file_path.stat()
        return {
            "name": file_path.name,
            "size": stat.st_size,
            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "extension": file_path.suffix,
            "path": str(file_path.relative_to(self.base_path))
        }
    
    def list_files(self, extension: Optional[str] = None) -> Dict[str, Any]:
        """List all files in the local-data directory."""
        try:
            files = []
            for file_path in self.base_path.iterdir():
                if file_path.is_file():
                    if extension is None or file_path.suffix == extension:
                        file_info = self._get_file_info(file_path)
                        files.append(file_info)
            
            # Sort by modified date (newest first)
            files.sort(key=lambda x: x.get('modified', ''), reverse=True)
            
            return {
                "success": True,
                "files": files,
                "total": len(files),
                "base_path": str(self.base_path)
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to list files: {str(e)}"
            }
    
    def read_file(self, filename: str) -> Dict[str, Any]:
        """Read content of a file."""
        try:
            if not self._is_safe_filename(filename):
                return {
                    "success": False,
                    "error": "Invalid filename"
                }
            
            file_path = self._get_file_path(filename)
            
            if not file_path.exists():
                return {
                    "success": False,
                    "error": "File not found"
                }
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            file_info = self._get_file_info(file_path)
            file_info["content"] = content
            
            return {
                "success": True,
                "file": file_info
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to read file: {str(e)}"
            }
    
    def create_file(self, filename: str, content: str) -> Dict[str, Any]:
        """Create a new file with content."""
        try:
            if not self._is_safe_filename(filename):
                return {
                    "success": False,
                    "error": "Invalid filename"
                }
            
            file_path = self._get_file_path(filename)
            
            if file_path.exists():
                return {
                    "success": False,
                    "error": "File already exists"
                }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            file_info = self._get_file_info(file_path)
            
            return {
                "success": True,
                "message": f"File '{filename}' created successfully",
                "file": file_info
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to create file: {str(e)}"
            }
    
    def update_file(self, filename: str, content: str) -> Dict[str, Any]:
        """Update content of an existing file."""
        try:
            if not self._is_safe_filename(filename):
                return {
                    "success": False,
                    "error": "Invalid filename"
                }
            
            file_path = self._get_file_path(filename)
            
            if not file_path.exists():
                return {
                    "success": False,
                    "error": "File not found"
                }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            file_info = self._get_file_info(file_path)
            
            return {
                "success": True,
                "message": f"File '{filename}' updated successfully",
                "file": file_info
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to update file: {str(e)}"
            }
    
    def delete_file(self, filename: str) -> Dict[str, Any]:
        """Delete a file."""
        try:
            if not self._is_safe_filename(filename):
                return {
                    "success": False,
                    "error": "Invalid filename"
                }
            
            file_path = self._get_file_path(filename)
            
            if not file_path.exists():
                return {
                    "success": False,
                    "error": "File not found"
                }
            
            file_path.unlink()
            
            return {
                "success": True,
                "message": f"File '{filename}' deleted successfully"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to delete file: {str(e)}"
            }
    
    def search_files(self, query: str) -> Dict[str, Any]:
        """Search for files containing the query string."""
        try:
            results = []
            query_lower = query.lower()
            
            for file_path in self.base_path.iterdir():
                if file_path.is_file() and file_path.suffix == '.txt':
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        if query_lower in content.lower():
                            file_info = self._get_file_info(file_path)
                            # Find the line containing the query
                            lines = content.split('\n')
                            matching_lines = []
                            for i, line in enumerate(lines, 1):
                                if query_lower in line.lower():
                                    matching_lines.append({
                                        "line_number": i,
                                        "line": line.strip()
                                    })
                            
                            file_info["matching_lines"] = matching_lines
                            file_info["match_count"] = len(matching_lines)
                            results.append(file_info)
                    except Exception:
                        # Skip files that can't be read
                        continue
            
            # Sort by match count (most matches first)
            results.sort(key=lambda x: x.get('match_count', 0), reverse=True)
            
            return {
                "success": True,
                "query": query,
                "results": results,
                "total_matches": len(results)
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to search files: {str(e)}"
            }
    
    def get_file_stats(self) -> Dict[str, Any]:
        """Get statistics about files in the directory."""
        try:
            files = list(self.base_path.iterdir())
            file_count = len([f for f in files if f.is_file()])
            
            total_size = 0
            extensions = {}
            
            for file_path in files:
                if file_path.is_file():
                    total_size += file_path.stat().st_size
                    ext = file_path.suffix or 'no_extension'
                    extensions[ext] = extensions.get(ext, 0) + 1
            
            return {
                "success": True,
                "stats": {
                    "total_files": file_count,
                    "total_size_bytes": total_size,
                    "total_size_mb": round(total_size / (1024 * 1024), 2),
                    "extensions": extensions,
                    "base_path": str(self.base_path)
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get file stats: {str(e)}"
            }

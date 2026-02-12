"""
MCP Filesystem tools for event planning
"""

import os
from typing import Dict, Any, Optional
from pathlib import Path

from nat.cli.register_workflow import register_function
from nat.builder.function_info import FunctionInfo
from nat.builder.builder import Builder
from nat.data_models.function import FunctionBaseConfig


class FilesystemConfig(
    FunctionBaseConfig,
    name="filesystem",
):
    """Configuration for MCP filesystem access"""
    allowed_directory: str = "/home/nshetty/Documents/event_planning_docs"



@register_function(config_type=FilesystemConfig)
async def filesystem(
    config: FilesystemConfig,
    builder: Builder,
):
    """Read and write files for event planning documents"""
    
    # Ensure directory exists
    Path(config.allowed_directory).mkdir(parents=True, exist_ok=True)
    
    async def _inner(
        action: str,
        filename: str = "",  # Made optional with default empty string
        content: str = ""
    ) -> Dict[str, Any]:
        """
        Filesystem operations for event planning.
        
        Args:
            action: 'read', 'write', or 'list'
            filename: Name of the file (not needed for 'list' action)
            content: Content to write (for write action)
        """
        
        # Handle list action (doesn't need filename)
        if action == "list":
            try:
                files = [f.name for f in Path(config.allowed_directory).iterdir() if f.is_file()]
                return {
                    "success": True,
                    "action": "list",
                    "files": files,
                    "count": len(files)
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e)
                }
        
        # For read/write actions, filename is required
        if not filename:
            return {
                "success": False,
                "error": f"filename is required for action '{action}'"
            }
        
        filepath = Path(config.allowed_directory) / filename
        
        # Security check - ensure file is within allowed directory
        if not str(filepath.resolve()).startswith(str(Path(config.allowed_directory).resolve())):
            return {
                "success": False,
                "error": "Access denied - file outside allowed directory"
            }
        
        try:
            if action == "read":
                if not filepath.exists():
                    return {
                        "success": False,
                        "error": f"File not found: {filename}"
                    }
                
                content = filepath.read_text()
                return {
                    "success": True,
                    "action": "read",
                    "filename": filename,
                    "content": content
                }
            
            elif action == "write":
                filepath.write_text(content)
                return {
                    "success": True,
                    "action": "write",
                    "filename": filename,
                    "message": f"Successfully wrote to {filename}"
                }
            
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}. Use 'read', 'write', or 'list'"
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    yield FunctionInfo.from_fn(
        _inner,
        description=(
            "Manage event planning documents. "
            "Actions: 'list' (show all files - no filename needed), "
            "'read' (read file content - requires filename), "
            "'write' (save content to file - requires filename and content). "
            "Files are stored in a dedicated event planning folder."
        )
    )

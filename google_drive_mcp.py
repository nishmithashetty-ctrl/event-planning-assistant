"""
Google Drive MCP Server for Event Planning
Provides tools to manage event documents via Google Drive API
"""

import os
import json
import httpx
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field, field_validator, ConfigDict

# Initialize MCP server
mcp = FastMCP("google_drive_mcp")

# Constants
GOOGLE_DRIVE_API_BASE = "https://www.googleapis.com/drive/v3"
GOOGLE_DRIVE_UPLOAD_BASE = "https://www.googleapis.com/upload/drive/v3"

# ============================================================
# Shared Utilities
# ============================================================

class ResponseFormat(str, Enum):
    """Output format for tool responses."""
    MARKDOWN = "markdown"
    JSON = "json"


def get_access_token() -> str:
    """Get Google Drive access token from environment."""
    token = os.getenv("GOOGLE_DRIVE_ACCESS_TOKEN")
    if not token:
        raise ValueError("GOOGLE_DRIVE_ACCESS_TOKEN environment variable not set")
    return token


async def make_drive_request(
    method: str,
    endpoint: str,
    params: Optional[Dict] = None,
    json_data: Optional[Dict] = None,
    files: Optional[Dict] = None
) -> Dict[str, Any]:
    """Make authenticated request to Google Drive API."""
    token = get_access_token()
    headers = {
        "Authorization": f"Bearer {token}",
    }
    
    if json_data and not files:
        headers["Content-Type"] = "application/json"
    
    url = f"{GOOGLE_DRIVE_API_BASE}/{endpoint}"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            if method == "GET":
                response = await client.get(url, headers=headers, params=params)
            elif method == "POST":
                if files:
                    response = await client.post(url, headers=headers, files=files, data=json_data, params=params)
                else:
                    response = await client.post(url, headers=headers, json=json_data, params=params)
            elif method == "PATCH":
                response = await client.patch(url, headers=headers, json=json_data, params=params)
            elif method == "DELETE":
                response = await client.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            
            # Handle empty responses (e.g., DELETE)
            if response.status_code == 204 or not response.content:
                return {"success": True}
            
            return response.json()
            
        except httpx.HTTPStatusError as e:
            error_detail = e.response.text
            if e.response.status_code == 401:
                return {"error": "Authentication failed. Please check your access token."}
            elif e.response.status_code == 403:
                return {"error": "Permission denied. Check that you have access to this resource."}
            elif e.response.status_code == 404:
                return {"error": "Resource not found. Please verify the file/folder ID."}
            elif e.response.status_code == 429:
                return {"error": "Rate limit exceeded. Please wait before making more requests."}
            return {"error": f"API request failed: {error_detail}"}
        except httpx.TimeoutException:
            return {"error": "Request timed out. Please try again."}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}


def format_file_info(file: Dict[str, Any], format_type: ResponseFormat) -> str:
    """Format file information based on response format."""
    if format_type == ResponseFormat.JSON:
        return json.dumps(file, indent=2)
    
    # Markdown format
    file_type = file.get("mimeType", "unknown")
    size = file.get("size", "N/A")
    if size != "N/A" and size.isdigit():
        size_mb = int(size) / (1024 * 1024)
        size = f"{size_mb:.2f} MB"
    
    created = file.get("createdTime", "Unknown")
    modified = file.get("modifiedTime", "Unknown")
    
    md = f"""## {file.get('name', 'Unnamed')}
**ID**: {file.get('id')}
**Type**: {file_type}
**Size**: {size}
**Created**: {created}
**Modified**: {modified}
**Web Link**: {file.get('webViewLink', 'N/A')}
"""
    return md


def format_file_list(files: List[Dict], format_type: ResponseFormat, total: int = 0) -> str:
    """Format list of files based on response format."""
    if format_type == ResponseFormat.JSON:
        return json.dumps({
            "files": files,
            "count": len(files),
            "total": total
        }, indent=2)
    
    # Markdown format
    md = f"# Files ({len(files)} shown"
    if total > 0:
        md += f", {total} total"
    md += ")\n\n"
    
    for file in files:
        name = file.get('name', 'Unnamed')
        file_id = file.get('id', 'N/A')
        mime_type = file.get('mimeType', 'unknown')
        modified = file.get('modifiedTime', 'Unknown')
        
        md += f"- **{name}** (`{file_id}`)\n"
        md += f"  - Type: {mime_type}\n"
        md += f"  - Modified: {modified}\n\n"
    
    return md


# ============================================================
# Tool: List Files
# ============================================================

class ListFilesInput(BaseModel):
    """Input parameters for listing files in Google Drive."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    query: Optional[str] = Field(
        default=None,
        description="Search query using Google Drive query syntax (e.g., \"name contains 'event'\" or \"mimeType='application/pdf'\")"
    )
    folder_id: Optional[str] = Field(
        default=None,
        description="List files within a specific folder ID"
    )
    limit: int = Field(
        default=20,
        description="Maximum number of files to return",
        ge=1,
        le=100
    )
    page_token: Optional[str] = Field(
        default=None,
        description="Page token for pagination (from previous response)"
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable"
    )


@mcp.tool(
    name="google_drive_list_files",
    annotations={
        "title": "List Files in Google Drive",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def google_drive_list_files(params: ListFilesInput) -> str:
    """List files in Google Drive with optional filtering.
    
    Search for event planning documents, filter by folder, or list all files.
    Supports pagination for large result sets.
    
    Args:
        params (ListFilesInput): Parameters including:
            - query: Optional search query
            - folder_id: Optional folder to search within
            - limit: Maximum results (1-100)
            - page_token: Pagination token
            - response_format: 'markdown' or 'json'
    
    Returns:
        str: Formatted list of files with metadata including:
            - File name, ID, type, size
            - Created/modified times
            - Web view links
            - Pagination info (next_page_token if more results exist)
    """
    # Build query
    query_parts = []
    if params.query:
        query_parts.append(params.query)
    
    if params.folder_id:
        query_parts.append(f"'{params.folder_id}' in parents")
    
    # Exclude trashed files
    query_parts.append("trashed=false")
    
    q = " and ".join(query_parts) if query_parts else None
    
    # Make API request
    api_params = {
        "pageSize": params.limit,
        "fields": "nextPageToken, files(id, name, mimeType, size, createdTime, modifiedTime, webViewLink)"
    }
    
    if q:
        api_params["q"] = q
    
    if params.page_token:
        api_params["pageToken"] = params.page_token
    
    result = await make_drive_request("GET", "files", params=api_params)
    
    if "error" in result:
        return f"Error: {result['error']}"
    
    files = result.get("files", [])
    next_token = result.get("nextPageToken")
    
    output = format_file_list(files, params.response_format)
    
    if next_token:
        output += f"\n**Next Page Token**: {next_token}\n"
        output += "Use this token in the `page_token` parameter to get the next page of results.\n"
    
    return output


# ============================================================
# Tool: Get File Details
# ============================================================

class GetFileInput(BaseModel):
    """Input parameters for getting file details."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    file_id: str = Field(
        ...,
        description="Google Drive file ID",
        min_length=1
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'"
    )


@mcp.tool(
    name="google_drive_get_file",
    annotations={
        "title": "Get File Details",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def google_drive_get_file(params: GetFileInput) -> str:
    """Get detailed information about a specific file.
    
    Retrieve complete metadata for an event document or file.
    
    Args:
        params (GetFileInput): Parameters including:
            - file_id: Google Drive file ID
            - response_format: 'markdown' or 'json'
    
    Returns:
        str: Detailed file information including name, type, size, dates, permissions, and links
    """
    result = await make_drive_request(
        "GET",
        f"files/{params.file_id}",
        params={
            "fields": "id, name, mimeType, size, createdTime, modifiedTime, webViewLink, "
                     "webContentLink, description, parents, owners, permissions"
        }
    )
    
    if "error" in result:
        return f"Error: {result['error']}"
    
    return format_file_info(result, params.response_format)


# ============================================================
# Tool: Create Folder
# ============================================================

class CreateFolderInput(BaseModel):
    """Input parameters for creating a folder."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    name: str = Field(
        ...,
        description="Folder name (e.g., 'Tech Conference 2026')",
        min_length=1,
        max_length=255
    )
    parent_folder_id: Optional[str] = Field(
        default=None,
        description="Parent folder ID (creates in root if not specified)"
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'"
    )


@mcp.tool(
    name="google_drive_create_folder",
    annotations={
        "title": "Create Folder",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def google_drive_create_folder(params: CreateFolderInput) -> str:
    """Create a new folder in Google Drive.
    
    Organize event planning documents by creating folders for different events or categories.
    
    Args:
        params (CreateFolderInput): Parameters including:
            - name: Folder name
            - parent_folder_id: Optional parent folder ID
            - response_format: 'markdown' or 'json'
    
    Returns:
        str: Created folder details including ID and web link
    """
    metadata = {
        "name": params.name,
        "mimeType": "application/vnd.google-apps.folder"
    }
    
    if params.parent_folder_id:
        metadata["parents"] = [params.parent_folder_id]
    
    result = await make_drive_request(
        "POST",
        "files",
        json_data=metadata,
        params={"fields": "id, name, webViewLink"}
    )
    
    if "error" in result:
        return f"Error: {result['error']}"
    
    return format_file_info(result, params.response_format)


# ============================================================
# Tool: Upload File
# ============================================================

class UploadFileInput(BaseModel):
    """Input parameters for uploading a file."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    name: str = Field(
        ...,
        description="File name with extension (e.g., 'event-plan.pdf')",
        min_length=1,
        max_length=255
    )
    content: str = Field(
        ...,
        description="File content (text content for now)"
    )
    mime_type: str = Field(
        default="text/plain",
        description="MIME type (e.g., 'text/plain', 'application/pdf')"
    )
    folder_id: Optional[str] = Field(
        default=None,
        description="Folder ID to upload into (root if not specified)"
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'"
    )


@mcp.tool(
    name="google_drive_upload_file",
    annotations={
        "title": "Upload File",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def google_drive_upload_file(params: UploadFileInput) -> str:
    """Upload a file to Google Drive.
    
    Upload event documents, participant lists, schedules, or other planning materials.
    
    Args:
        params (UploadFileInput): Parameters including:
            - name: File name with extension
            - content: File content (text)
            - mime_type: MIME type of the file
            - folder_id: Optional folder to upload into
            - response_format: 'markdown' or 'json'
    
    Returns:
        str: Uploaded file details including ID and web link
    """
    metadata = {
        "name": params.name,
        "mimeType": params.mime_type
    }
    
    if params.folder_id:
        metadata["parents"] = [params.folder_id]
    
    # For simple file upload using multipart
    token = get_access_token()
    headers = {
        "Authorization": f"Bearer {token}",
    }
    
    # Create multipart upload
    files = {
        'metadata': (None, json.dumps(metadata), 'application/json'),
        'file': (params.name, params.content.encode(), params.mime_type)
    }
    
    url = f"{GOOGLE_DRIVE_UPLOAD_BASE}/files"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                url,
                headers=headers,
                files=files,
                params={"uploadType": "multipart", "fields": "id, name, mimeType, webViewLink"}
            )
            response.raise_for_status()
            result = response.json()
            
            return format_file_info(result, params.response_format)
            
        except httpx.HTTPStatusError as e:
            return f"Error: Upload failed with status {e.response.status_code}: {e.response.text}"
        except Exception as e:
            return f"Error: {str(e)}"


# ============================================================
# Tool: Delete File
# ============================================================

class DeleteFileInput(BaseModel):
    """Input parameters for deleting a file."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    file_id: str = Field(
        ...,
        description="Google Drive file ID to delete",
        min_length=1
    )


@mcp.tool(
    name="google_drive_delete_file",
    annotations={
        "title": "Delete File",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def google_drive_delete_file(params: DeleteFileInput) -> str:
    """Delete a file from Google Drive.
    
    Remove outdated event documents or files. This operation is permanent.
    
    Args:
        params (DeleteFileInput): Parameters including:
            - file_id: ID of file to delete
    
    Returns:
        str: Confirmation message
    """
    result = await make_drive_request("DELETE", f"files/{params.file_id}")
    
    if "error" in result:
        return f"Error: {result['error']}"
    
    return f"Successfully deleted file with ID: {params.file_id}"


# ============================================================
# Tool: Search Files
# ============================================================

class SearchFilesInput(BaseModel):
    """Input parameters for searching files."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    search_term: str = Field(
        ...,
        description="Search term to find in file names (e.g., 'conference', 'participant list')",
        min_length=1
    )
    limit: int = Field(
        default=10,
        description="Maximum number of results",
        ge=1,
        le=50
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'"
    )


@mcp.tool(
    name="google_drive_search_files",
    annotations={
        "title": "Search Files",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def google_drive_search_files(params: SearchFilesInput) -> str:
    """Search for files by name in Google Drive.
    
    Find event documents quickly by searching for keywords in file names.
    
    Args:
        params (SearchFilesInput): Parameters including:
            - search_term: Text to search for in file names
            - limit: Maximum results to return
            - response_format: 'markdown' or 'json'
    
    Returns:
        str: List of matching files with details
    """
    query = f"name contains '{params.search_term}' and trashed=false"
    
    result = await make_drive_request(
        "GET",
        "files",
        params={
            "q": query,
            "pageSize": params.limit,
            "fields": "files(id, name, mimeType, modifiedTime, webViewLink)"
        }
    )
    
    if "error" in result:
        return f"Error: {result['error']}"
    
    files = result.get("files", [])
    
    if not files:
        return f"No files found matching '{params.search_term}'"
    
    return format_file_list(files, params.response_format, total=len(files))


# ============================================================
# Main Entry Point
# ============================================================

if __name__ == "__main__":
    # Run with stdio transport for local integration
    mcp.run()

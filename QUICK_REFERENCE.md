# Quick Reference Card - Google Drive MCP Integration

## Setup (One-time)

```bash
# 1. Install dependencies
pip install -r requirements.txt --break-system-packages

# 2. Get Google Drive token from OAuth Playground
# https://developers.google.com/oauthplayground/

# 3. Set environment variable
export GOOGLE_DRIVE_ACCESS_TOKEN="your_token_here"

# 4. Run setup
./setup.sh

# 5. Test
python test_integration.py
```

## Running Your Agent

```bash
nat-cli run config_react_with_gdrive.yml
```

## Common Agent Commands

| What You Want | Example Query |
|--------------|---------------|
| List files | "List all files in Google Drive" |
| Search files | "Search for files containing 'conference'" |
| Create folder | "Create a folder called Tech Event 2026" |
| Upload file | "Upload the participant list to Google Drive" |
| Get file info | "Show me details for file abc123xyz" |
| Delete file | "Delete the file with ID abc123xyz" |

## Tool Quick Reference

```python
# List files
gdrive_list_files
  - query: "name contains 'event'"
  - folder_id: "folder123"
  - limit: 20

# Search
gdrive_search_files
  - search_term: "conference"
  - limit: 10

# Get file
gdrive_get_file
  - file_id: "abc123"

# Create folder
gdrive_create_folder
  - name: "Event 2026"
  - parent_folder_id: "parent123"  # optional

# Upload
gdrive_upload_file
  - name: "file.csv"
  - content: "data..."
  - mime_type: "text/csv"
  - folder_id: "folder123"  # optional

# Delete
gdrive_delete_file
  - file_id: "abc123"
```

## Troubleshooting Quick Fixes

| Problem | Solution |
|---------|----------|
| Token not set | `export GOOGLE_DRIVE_ACCESS_TOKEN="token"` |
| Auth failed | Get new token (expires 1hr) |
| MCP error | `python google_drive_mcp.py --help` |
| Import error | `pip install mcp --break-system-packages` |

## File Structure

```
project/
├── google_drive_mcp.py              # MCP server
├── google_drive_mcp_integration.py  # NAT integration
├── config_react_with_gdrive.yml     # Config
├── requirements.txt                 # Dependencies
├── setup.sh                         # Setup script
├── test_integration.py              # Tests
├── README.md                        # Main docs
└── INTEGRATION_GUIDE.md            # Detailed guide
```

## Important Notes

- ⚠️ OAuth Playground tokens expire after 1 hour
- 🔒 Never commit access tokens to git
- 📝 Use service accounts for production
- ✅ Run `./setup.sh` before first use
- 🧪 Test with `python test_integration.py`

## Need Help?

1. Check `README.md` for quick start
2. Read `INTEGRATION_GUIDE.md` for details
3. Run `python test_integration.py` to diagnose
4. Verify Google Drive API is enabled

## Example Workflow

```bash
# 1. Start agent
nat-cli run config_react_with_gdrive.yml

# 2. Create folder
>>> "Create a folder for Tech Conference 2026"

# 3. Upload documents
>>> "Upload the participant list to the conference folder"

# 4. Search files
>>> "Find all files related to the conference"

# 5. Share links
>>> "Give me the shareable link for the participant list"
```

## MIME Types Reference

| File Type | MIME Type |
|-----------|-----------|
| Text | `text/plain` |
| CSV | `text/csv` |
| JSON | `application/json` |
| PDF | `application/pdf` |
| Word | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| Excel | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |

## Support Resources

- MCP Docs: https://modelcontextprotocol.io/
- Drive API: https://developers.google.com/drive/api
- NAT Docs: NVIDIA NeMo documentation
- OAuth: https://developers.google.com/oauthplayground/

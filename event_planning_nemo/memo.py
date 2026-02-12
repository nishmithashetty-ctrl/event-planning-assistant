"""
Memory Storage Tool for Event Planning Agent
"""

import json
import os
from typing import Dict, Any, List
from datetime import datetime

from nat.cli.register_workflow import register_function
from nat.builder.function_info import FunctionInfo
from nat.builder.builder import Builder
from nat.data_models.function import FunctionBaseConfig


# ============================================================
# Memory Storage Tool
# ============================================================

class MemoryConfig(
    FunctionBaseConfig,
    name="memory_storage",
):
    storage_path: str = "./conversation_memory.json"
    max_history: int = 10


@register_function(config_type=MemoryConfig)
async def memory_storage(
    config: MemoryConfig,
    builder: Builder,
):
    def load_memory() -> List[Dict]:
        """Load conversation history from file"""
        if os.path.exists(config.storage_path):
            try:
                with open(config.storage_path, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return []
        return []
    
    def save_memory(history: List[Dict]):
        """Save conversation history to file"""
        storage_dir = os.path.dirname(config.storage_path)
        if storage_dir:
            os.makedirs(storage_dir, exist_ok=True)
        with open(config.storage_path, 'w') as f:
            json.dump(history[-config.max_history:], f, indent=2)
    
    async def _inner(
        action: str,
        message: str = "",
        role: str = "user",
        query: str = ""
    ) -> Dict[str, Any]:
        """
        Memory management tool
        Actions:
        - save: Save a message to memory
        - recall: Get recent conversation history
        - search: Search memory for specific content
        - clear: Clear all memory
        """
        history = load_memory()
        
        if action == "save":
            history.append({
                "role": role,
                "content": message,
                "timestamp": datetime.now().isoformat()
            })
            save_memory(history)
            return {
                "success": True,
                "message": "Memory saved",
                "total_messages": len(history)
            }
        
        elif action == "recall":
            return {
                "success": True,
                "history": history[-5:],  # Last 5 exchanges
                "total_messages": len(history)
            }
        
        elif action == "search":
            if not query:
                return {"success": False, "error": "Query required for search"}
            
            results = [
                msg for msg in history
                if query.lower() in msg["content"].lower()
            ]
            return {
                "success": True,
                "results": results,
                "count": len(results)
            }
        
        elif action == "clear":
            save_memory([])
            return {
                "success": True,
                "message": "Memory cleared"
            }
        
        return {
            "success": False,
            "error": f"Unknown action: {action}"
        }
    
    yield FunctionInfo.from_fn(
        _inner,
        description="Manage conversation memory. Actions: save, recall, search, clear",
    )
"""
NAT tool registration for Event Planning Agent
"""

import os
import json
import sqlite3
import requests
from datetime import datetime
from typing import List, Optional, Dict, Any

from nat.cli.register_workflow import register_function
from nat.builder.function_info import FunctionInfo
from nat.builder.builder import Builder
from nat.data_models.function import FunctionBaseConfig
from nat.builder.framework_enum import LLMFrameworkEnum
from langchain_core.messages import SystemMessage, HumanMessage

# Import to register tools
from .memo import memory_storage, MemoryConfig

# REMOVE THIS LINE - NAT handles MCP integration automatically:
# from .google_drive_mcp_integration import *

# ============================================================
# Generate Event Themes
# ============================================================

class GenerateEventThemesConfig(
    FunctionBaseConfig,
    name="generate_event_themes",
):
    llm_name: str


@register_function(config_type=GenerateEventThemesConfig)
async def generate_event_themes(
    config: GenerateEventThemesConfig,
    builder: Builder,
):
    async def _inner(event_idea: str) -> Dict[str, Any]:
        llm = await builder.get_llm(
            config.llm_name,
            wrapper_type=LLMFrameworkEnum.LANGCHAIN,
        )

        messages = [
            SystemMessage(
                content=(
                    "Generate EXACTLY 5 creative event themes.\n"
                    "Return ONLY a valid JSON array of strings."
                )
            ),
            HumanMessage(content=f"Generate themes for {event_idea}"),
        ]

        response = await llm.ainvoke(messages)
        themes = json.loads(response.content)

        if not isinstance(themes, list) or len(themes) != 5:
            raise ValueError("LLM must return exactly 5 themes")

        return {"themes": themes}

    yield FunctionInfo.from_fn(
        _inner,
        description="Generate 5 creative event themes",
    )


# ============================================================
#Filesystem Tool
# ============================================================

class FilesystemConfig(
    FunctionBaseConfig,
    name="filesystem",
):
    allowed_directory: str = "/tmp/event_planning"


@register_function(config_type=FilesystemConfig)
async def filesystem(
    config: FilesystemConfig,
    builder: Builder,
):
    async def _inner(
        action: str,
        filename: str = "",
        content: str = "",
    ) -> Dict[str, Any]:
        os.makedirs(config.allowed_directory, exist_ok=True)

        if action == "list":
            files = [
                f for f in os.listdir(config.allowed_directory)
                if os.path.isfile(os.path.join(config.allowed_directory, f))
            ]
            return {"success": True, "files": files, "count": len(files)}

        if action == "read":
            if not filename:
                return {"success": False, "error": "filename required for read"}
            path = os.path.join(config.allowed_directory, filename)
            if not os.path.exists(path):
                return {"success": False, "error": "File not found"}
            with open(path) as f:
                return {"success": True, "content": f.read()}

        if action == "write":
            if not filename:
                return {"success": False, "error": "filename required for write"}
            path = os.path.join(config.allowed_directory, filename)
            with open(path, "w") as f:
                f.write(content)
            return {"success": True, "message": f"Saved to {filename}"}

        return {"success": False, "error": "Unknown action"}

    yield FunctionInfo.from_fn(
        _inner,
        description="Manage event planning documents. Actions: list, read, write",
    )


# ============================================================
# Save Participant
# ============================================================

class SaveParticipantConfig(
    FunctionBaseConfig,
    name="save_participant",
):
    database_path: str = "event_planning.db"


@register_function(config_type=SaveParticipantConfig)
async def save_participant(
    config: SaveParticipantConfig,
    builder: Builder,
):
    async def _inner(
        name: str,
        email: str,
        company: str = "",
        role: str = "",
        phone: str = "",
    ) -> Dict[str, Any]:
        try:
            conn = sqlite3.connect(config.database_path)
            cursor = conn.cursor()
            
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS participants (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    company TEXT,
                    role TEXT,
                    phone TEXT,
                    created_at TIMESTAMP
                )
                """
            )
            
            cursor.execute(
                """
                INSERT INTO participants (name, email, company, role, phone, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (name, email, company, role, phone, datetime.now()),
            )
            
            conn.commit()
            participant_id = cursor.lastrowid
            conn.close()
            
            return {
                "success": True,
                "message": f"Participant '{name}' saved successfully",
                "participant_id": participant_id,
            }
            
        except sqlite3.IntegrityError:
            return {
                "success": False,
                "message": f"Email '{email}' already exists",
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Database error: {str(e)}",
            }

    yield FunctionInfo.from_fn(
        _inner,
        description="Save a participant to the event database",
    )


# ============================================================
# Get Participants
# ============================================================

class GetParticipantsConfig(
    FunctionBaseConfig,
    name="get_participants",
):
    database_path: str = "event_planning.db"


@register_function(config_type=GetParticipantsConfig)
async def get_participants(
    config: GetParticipantsConfig,
    builder: Builder,
):
    async def _inner(limit: int = 10) -> Dict[str, Any]:
        conn = sqlite3.connect(config.database_path)
        cursor = conn.cursor()
        
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS participants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                company TEXT,
                role TEXT,
                phone TEXT,
                created_at TIMESTAMP
            )
            """
        )

        cursor.execute(
            """
            SELECT id, name, email, company, role
            FROM participants
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        )

        rows = cursor.fetchall()
        cursor.execute("SELECT COUNT(*) FROM participants")
        total_count = cursor.fetchone()[0]
        conn.close()

        return {
            "participants": [
                {
                    "id": r[0],
                    "name": r[1],
                    "email": r[2],
                    "company": r[3],
                    "role": r[4],
                }
                for r in rows
            ],
            "total_count": total_count,
        }

    yield FunctionInfo.from_fn(
        _inner,
        description="Retrieve participants from the event database",
    )


# ============================================================
# Check Weather
# ============================================================

class CheckWeatherConfig(
    FunctionBaseConfig,
    name="check_weather",
):
    api_key: Optional[str] = None


@register_function(config_type=CheckWeatherConfig)
async def check_weather(
    config: CheckWeatherConfig,
    builder: Builder,
):
    async def _inner(city: str, country_code: str = "US") -> Dict[str, Any]:
        api_key = config.api_key or os.getenv("OPENWEATHER_API_KEY")
        if not api_key:
            return {"success": False, "error": "Missing API key"}
        
        try:
            response = requests.get(
                "http://api.openweathermap.org/data/2.5/weather",
                params={"q": f"{city},{country_code}", "appid": api_key, "units": "metric"},
                timeout=10,
            )
            if response.status_code != 200:
                return {"success": False, "error": response.text}
            
            data = response.json()
            return {
                "success": True,
                "city": data["name"],
                "temperature_celsius": round(data["main"]["temp"], 1),
                "conditions": data["weather"][0]["main"],
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    yield FunctionInfo.from_fn(
        _inner,
        description="Check weather conditions for event planning",
    )
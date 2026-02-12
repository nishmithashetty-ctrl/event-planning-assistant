import sqlite3
from datetime import datetime
from pydantic import BaseModel, Field
from nat.cli.register_workflow import register_function
from nat.builder.function_info import FunctionInfo
from nat.data_models.function import FunctionBaseConfig
from nat.builder.builder import Builder

# ============= Save Participant Tool =============
class SaveParticipantInput(BaseModel):
    name: str = Field(description="Participant's full name")
    email: str = Field(description="Participant's email address")
    company: str = Field(default="", description="Participant's company")
    role: str = Field(default="", description="Participant's role")
    phone: str = Field(default="", description="Participant's phone number")

class SaveParticipantOutput(BaseModel):
    success: bool
    message: str
    participant_id: int = None

class SaveParticipantConfig(FunctionBaseConfig, name="save_participant"):
    database_path: str = "event_planning.db"

@register_function(config_type=SaveParticipantConfig)
async def save_participant(config: SaveParticipantConfig, builder: Builder):
    async def _inner(input_data: SaveParticipantInput) -> SaveParticipantOutput:
        try:
            conn = sqlite3.connect(config.database_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO participants (name, email, company, role, phone, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                input_data.name,
                input_data.email,
                input_data.company,
                input_data.role,
                input_data.phone,
                datetime.now()
            ))
            
            participant_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return SaveParticipantOutput(
                success=True,
                message=f"Participant '{input_data.name}' saved successfully!",
                participant_id=participant_id
            )
        except sqlite3.IntegrityError:
            return SaveParticipantOutput(
                success=False,
                message=f"Email '{input_data.email}' already exists!"
            )
        except Exception as e:
            return SaveParticipantOutput(
                success=False,
                message=f"Error saving participant: {str(e)}"
            )
    
    yield FunctionInfo.from_fn(
        _inner,
        description="Save a participant to the event database"
    )

# ============= Get Participants Tool =============
class GetParticipantsInput(BaseModel):
    limit: int = Field(default=10, description="Number of participants to retrieve")

class Participant(BaseModel):
    id: int
    name: str
    email: str
    company: str
    role: str

class GetParticipantsOutput(BaseModel):
    participants: list[Participant]
    total_count: int

class GetParticipantsConfig(FunctionBaseConfig, name="get_participants"):
    database_path: str = "event_planning.db"

@register_function(config_type=GetParticipantsConfig)
async def get_participants(config: GetParticipantsConfig, builder: Builder):
    async def _inner(input_data: GetParticipantsInput) -> GetParticipantsOutput:
        try:
            conn = sqlite3.connect(config.database_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, name, email, company, role 
                FROM participants 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (input_data.limit,))
            
            rows = cursor.fetchall()
            participants = [
                Participant(id=row[0], name=row[1], email=row[2], company=row[3], role=row[4])
                for row in rows
            ]
            
            cursor.execute("SELECT COUNT(*) FROM participants")
            total_count = cursor.fetchone()[0]
            
            conn.close()
            
            return GetParticipantsOutput(
                participants=participants,
                total_count=total_count
            )
        except Exception as e:
            return GetParticipantsOutput(
                participants=[],
                total_count=0
            )
    
    yield FunctionInfo.from_fn(
        _inner,
        description="Retrieve participants from the event database"
    )

"""
Meeting Agent - Analysis Schemas
=================================

This module defines Pydantic schemas for analysis data validation and
serialization. Schemas handle API request/response data formatting.

Packages Used:
    - pydantic: Data validation and serialization
        - BaseModel: Base class for all schemas
        - ConfigDict: Configuration for schema behavior
        - Field: Field metadata and validation

Key Components:
    - ActionItem: Schema for a single action item
    - AnalysisBase: Base schema with common analysis fields
    - AnalysisCreate: Schema for creating a new analysis
    - AnalysisResponse: Schema for API responses
    - AnalysisSummary: Minimal schema for listings

Usage:
    from app.schemas.analysis import AnalysisResponse, ActionItem

    # In API endpoint
    @router.get("/recordings/{id}/analysis", response_model=AnalysisResponse)
    def get_analysis(id: int, db: Session = Depends(get_db)):
        recording = db.query(Recording).get(id)
        return recording.analysis
"""

from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import datetime


# -----------------------------------------------------------------------------
# Action Item Schema
# -----------------------------------------------------------------------------

class ActionItem(BaseModel):
    """
    Schema for a single action item extracted from the meeting.

    Attributes:
        speaker (str): Person assigned to this action
        task (str): Description of the action/task
        due_date (str): Optional due date mentioned
        priority (str): Optional priority level (high, medium, low)

    Example:
        {
            "speaker": "John",
            "task": "Send the quarterly report to the team",
            "due_date": "Friday",
            "priority": "high"
        }
    """
    speaker: str = Field(..., description="Person assigned to this action")
    task: str = Field(..., description="Description of the task")
    due_date: Optional[str] = Field(None, description="Due date if mentioned")
    priority: Optional[str] = Field(None, description="Priority level")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "speaker": "John",
                "task": "Send the quarterly report",
                "due_date": "Friday",
                "priority": "high"
            }
        }
    )


# -----------------------------------------------------------------------------
# Base Analysis Schema
# -----------------------------------------------------------------------------

class AnalysisBase(BaseModel):
    """
    Base schema with common analysis fields.

    Contains fields shared between create and response schemas.
    """
    summary: str = Field(default="", description="Concise meeting summary")
    action_items: List[ActionItem] = Field(
        default_factory=list,
        description="List of action items with speaker attribution"
    )
    decisions: List[str] = Field(
        default_factory=list,
        description="Key decisions made during the meeting"
    )
    key_topics: List[str] = Field(
        default_factory=list,
        description="Main topics discussed"
    )


# -----------------------------------------------------------------------------
# Create Schema
# -----------------------------------------------------------------------------

class AnalysisCreate(AnalysisBase):
    """
    Schema for creating a new analysis.

    Used when saving analysis results to the database.

    Attributes:
        recording_id (int): ID of the associated recording
        summary (str): Meeting summary
        action_items (list): List of action items
        decisions (list): List of decisions
        key_topics (list): List of topics
        model_used (str): Name of the LLM model used

    Example:
        analysis_data = AnalysisCreate(
            recording_id=1,
            summary="Team discussed Q4 goals.",
            action_items=[
                ActionItem(speaker="John", task="Prepare slides")
            ],
            decisions=["Use PostgreSQL"],
            model_used="mistral"
        )
    """
    recording_id: int = Field(..., gt=0, description="Recording ID")
    model_used: Optional[str] = Field(None, description="LLM model used")


# -----------------------------------------------------------------------------
# Response Schema
# -----------------------------------------------------------------------------

class AnalysisResponse(AnalysisBase):
    """
    Schema for analysis API responses.

    Includes all analysis data plus metadata fields.

    Attributes:
        id (int): Analysis database ID
        recording_id (int): Associated recording ID
        summary (str): Meeting summary
        action_items (list): List of action items
        decisions (list): List of decisions
        key_topics (list): List of topics
        model_used (str): LLM model used
        created_at (datetime): When analysis was created

    Example Response:
        {
            "id": 1,
            "recording_id": 1,
            "summary": "Team discussed Q4 goals and assigned tasks.",
            "action_items": [
                {"speaker": "John", "task": "Prepare slides", ...}
            ],
            "decisions": ["Use PostgreSQL"],
            "key_topics": ["Q4 planning", "Database selection"],
            "model_used": "mistral",
            "created_at": "2024-01-15T10:30:00Z"
        }
    """
    id: int
    recording_id: int
    model_used: Optional[str] = None
    created_at: datetime

    # Enable ORM mode for SQLAlchemy model serialization
    model_config = ConfigDict(from_attributes=True)


# -----------------------------------------------------------------------------
# Summary Schema (for listing)
# -----------------------------------------------------------------------------

class AnalysisSummary(BaseModel):
    """
    Minimal analysis info for listing views.

    Used when including analysis info with recording lists
    without sending full action items and decisions.

    Attributes:
        id (int): Analysis ID
        summary (str): Meeting summary (truncated)
        action_item_count (int): Number of action items
        decision_count (int): Number of decisions
        has_analysis (bool): Whether analysis exists
    """
    id: int
    summary: str = ""
    action_item_count: int = 0
    decision_count: int = 0

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_analysis(cls, analysis) -> "AnalysisSummary":
        """
        Create summary from an Analysis model instance.

        Args:
            analysis: Analysis model instance

        Returns:
            AnalysisSummary: Summary of the analysis
        """
        # Truncate summary if too long
        summary = analysis.summary or ""
        if len(summary) > 200:
            summary = summary[:197] + "..."

        return cls(
            id=analysis.id,
            summary=summary,
            action_item_count=len(analysis.action_items) if analysis.action_items else 0,
            decision_count=len(analysis.decisions) if analysis.decisions else 0
        )

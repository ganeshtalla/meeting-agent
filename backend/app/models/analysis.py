"""
Meeting Agent - Analysis Model
===============================

This module defines the SQLAlchemy ORM model for storing LLM analysis results.
The Analysis model stores summaries, action items, and decisions extracted
from meeting transcripts.

Packages Used:
    - sqlalchemy: SQL toolkit and ORM
        - Column: Defines a database column
        - Integer, String, Text, DateTime, JSON: Column types
        - ForeignKey: Defines foreign key relationship
    - sqlalchemy.orm: ORM relationship management
        - relationship: Defines model relationships
    - sqlalchemy.sql: SQL expression elements
        - func: SQL function constructs

Key Components:
    - Analysis: SQLAlchemy model for analysis results

Table Schema:
    CREATE TABLE analyses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        recording_id INTEGER NOT NULL REFERENCES recordings(id),
        summary TEXT NOT NULL,
        action_items JSON NOT NULL,
        decisions JSON NOT NULL,
        key_topics JSON NOT NULL,
        model_used VARCHAR(100),
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )

Action Items JSON Structure:
    [
        {
            "speaker": "John",
            "task": "Send the report",
            "due_date": "Friday",
            "priority": "high"
        }
    ]

Usage:
    from app.models.analysis import Analysis

    # Create an analysis record
    analysis = Analysis(
        recording_id=1,
        summary="Team discussed Q4 goals and assigned tasks.",
        action_items=[
            {"speaker": "John", "task": "Prepare presentation"}
        ],
        decisions=["Use PostgreSQL for the new project"],
        key_topics=["Q4 planning", "Database selection"]
    )
    db.add(analysis)
    db.commit()
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class Analysis(Base):
    """
    SQLAlchemy model for storing meeting analysis results.

    This model stores the LLM-generated analysis including summary,
    action items, decisions, and key topics.

    Attributes:
        id (int): Primary key, auto-incremented
        recording_id (int): Foreign key to the recordings table
        summary (str): Concise summary of the meeting
        action_items (list): JSON array of action items
        decisions (list): JSON array of decisions made
        key_topics (list): JSON array of topics discussed
        model_used (str): Name of the LLM model used
        created_at (datetime): Timestamp when analysis was created

    Relationships:
        recording: Many-to-one relationship with Recording model

    Table Name:
        'analyses'

    Indexes:
        - Primary key index on 'id'
        - Foreign key index on 'recording_id'
    """

    # -------------------------------------------------------------------------
    # Table Configuration
    # -------------------------------------------------------------------------
    __tablename__ = "analyses"

    # -------------------------------------------------------------------------
    # Primary Key
    # -------------------------------------------------------------------------
    id = Column(Integer, primary_key=True, index=True)

    # -------------------------------------------------------------------------
    # Foreign Key Relationship
    # -------------------------------------------------------------------------
    # Reference to the parent recording
    # ondelete="CASCADE" ensures analysis is deleted when recording is deleted
    recording_id = Column(
        Integer,
        ForeignKey("recordings.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # -------------------------------------------------------------------------
    # Analysis Content
    # -------------------------------------------------------------------------
    # Concise summary of the meeting (2-3 sentences)
    summary = Column(Text, nullable=False, default="")

    # Action items extracted from the meeting
    # Each item: {"speaker": str, "task": str, "due_date": str|null, "priority": str|null}
    action_items = Column(JSON, nullable=False, default=list)

    # Key decisions made during the meeting
    decisions = Column(JSON, nullable=False, default=list)

    # Main topics discussed
    key_topics = Column(JSON, nullable=False, default=list)

    # -------------------------------------------------------------------------
    # Metadata
    # -------------------------------------------------------------------------
    # Name of the LLM model used for analysis
    model_used = Column(String(100), nullable=True)

    # -------------------------------------------------------------------------
    # Timestamps
    # -------------------------------------------------------------------------
    # When the analysis was created
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # -------------------------------------------------------------------------
    # Relationships
    # -------------------------------------------------------------------------
    # back_populates creates a bidirectional relationship
    recording = relationship("Recording", back_populates="analysis")

    # -------------------------------------------------------------------------
    # Helper Methods
    # -------------------------------------------------------------------------

    def get_action_items_for_speaker(self, speaker: str) -> list:
        """
        Get action items assigned to a specific speaker.

        Args:
            speaker: Speaker name to filter by

        Returns:
            list: Action items for the specified speaker
        """
        return [
            item for item in self.action_items
            if item.get("speaker", "").lower() == speaker.lower()
        ]

    def get_high_priority_items(self) -> list:
        """
        Get action items marked as high priority.

        Returns:
            list: High priority action items
        """
        return [
            item for item in self.action_items
            if item.get("priority", "").lower() == "high"
        ]

    @property
    def action_item_count(self) -> int:
        """Get the number of action items."""
        return len(self.action_items) if self.action_items else 0

    @property
    def decision_count(self) -> int:
        """Get the number of decisions."""
        return len(self.decisions) if self.decisions else 0

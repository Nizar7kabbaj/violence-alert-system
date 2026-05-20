from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class AlertIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    video_path: str
    confidence: float = Field(ge=0.0, le=1.0)
    frame_count: int = Field(ge=1)
    camera_id: str
    label: str = "violence"
    snapshot_path: Optional[str] = None


class AlertOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    video_path: str
    confidence: float
    frame_count: int
    label: str
    camera_id: str
    timestamp: datetime
    reviewed: bool
    snapshot_path: Optional[str] = None
    notified: bool = False


class AlertDB(BaseModel):
    model_config = ConfigDict(extra="forbid")

    video_path: str
    confidence: float
    frame_count: int
    label: str = "violence"
    camera_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    reviewed: bool = False
    snapshot_path: Optional[str] = None
    notified: bool = False
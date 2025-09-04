from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum


class LogLevel(str, Enum):
    ERROR = "ERROR"
    WARN = "WARN"
    WARNING = "WARNING"
    INFO = "INFO"
    DEBUG = "DEBUG"
    TRACE = "TRACE"
    FATAL = "FATAL"
    CRITICAL = "CRITICAL"


class LogFormat(str, Enum):
    JSON = "json"
    CSV = "csv"
    SYSLOG = "syslog"
    PLAIN_TEXT = "plain_text"
    CUSTOM = "custom"


class FileUploadResponse(BaseModel):
    id: str
    filename: str
    size: int
    format: LogFormat
    upload_time: datetime
    status: str = "uploaded"


class LogEntry(BaseModel):
    timestamp: Optional[datetime] = None
    level: Optional[LogLevel] = None
    service: Optional[str] = None
    message: str
    raw_line: str
    line_number: int
    metadata: Dict[str, Any] = Field(default_factory=dict)


class LogAnalysis(BaseModel):
    total_entries: int
    date_range: Dict[str, Optional[datetime]]
    level_distribution: Dict[LogLevel, int]
    service_distribution: Dict[str, int]
    error_patterns: List[Dict[str, Any]]
    anomalies: List[Dict[str, Any]]
    time_series: List[Dict[str, Any]]


class PatternMatch(BaseModel):
    pattern: str
    count: int
    examples: List[str]
    severity: str
    category: str
    first_occurrence: Optional[datetime] = None
    last_occurrence: Optional[datetime] = None


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)


class ChatRequest(BaseModel):
    message: str
    file_id: Optional[str] = None
    session_id: Optional[str] = "default"
    context: Optional[List[ChatMessage]] = None


class ChatResponse(BaseModel):
    response: str
    context: List[ChatMessage]
    suggested_questions: Optional[List[str]] = None


class AnalysisRequest(BaseModel):
    file_id: str
    analysis_type: Optional[str] = "full"
    filters: Optional[Dict[str, Any]] = None


class FileInfo(BaseModel):
    id: str
    filename: str
    size: int
    format: LogFormat
    upload_time: datetime
    status: str
    analysis: Optional[LogAnalysis] = None
    entry_count: Optional[int] = None


class TimeSeriesData(BaseModel):
    timestamp: str
    error_count: int
    warn_count: int
    info_count: int
    total_count: int


class ErrorResponse(BaseModel):
    detail: str
    error_type: str
    timestamp: datetime = Field(default_factory=datetime.now)
import os
import json
import csv
import re
from typing import Optional
from app.models.schemas import LogFormat
from app.core.config import settings


def validate_file_size(size: int) -> bool:
    """Validate file size against maximum allowed size"""
    return size <= settings.MAX_FILE_SIZE


def get_file_format(content: bytes, filename: str) -> LogFormat:
    """Detect log file format based on content and filename"""
    
    # Get file extension
    _, ext = os.path.splitext(filename.lower())
    
    # Try to decode content as text
    try:
        text_content = content.decode('utf-8', errors='ignore')[:1000]  # First 1KB for detection
    except:
        return LogFormat.CUSTOM
    
    # JSON format detection
    if ext == '.json' or _is_json_format(text_content):
        return LogFormat.JSON
    
    # CSV format detection
    if ext == '.csv' or _is_csv_format(text_content):
        return LogFormat.CSV
    
    # Syslog format detection
    if ext == '.syslog' or _is_syslog_format(text_content):
        return LogFormat.SYSLOG
    
    # Default to plain text
    return LogFormat.PLAIN_TEXT


def _is_json_format(content: str) -> bool:
    """Check if content appears to be JSON format"""
    lines = content.strip().split('\n')[:5]  # Check first 5 lines
    
    json_line_count = 0
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            json.loads(line)
            json_line_count += 1
        except:
            continue
    
    return json_line_count >= max(1, len([l for l in lines if l.strip()]) // 2)


def _is_csv_format(content: str) -> bool:
    """Check if content appears to be CSV format"""
    lines = content.strip().split('\n')[:5]
    if len(lines) < 2:
        return False
    
    try:
        # Try to parse as CSV
        dialect = csv.Sniffer().sniff(content[:500])
        reader = csv.reader(lines[:3], dialect)
        rows = list(reader)
        
        # Check if we have consistent column counts
        if len(rows) >= 2:
            first_row_cols = len(rows[0])
            return all(len(row) == first_row_cols for row in rows[1:])
    except:
        pass
    
    return False


def _is_syslog_format(content: str) -> bool:
    """Check if content appears to be syslog format"""
    lines = content.strip().split('\n')[:5]
    
    # Common syslog patterns
    syslog_patterns = [
        r'^\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}',  # Jan 01 12:00:00
        r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}',  # ISO timestamp
        r'<\d+>',  # Priority value
    ]
    
    matching_lines = 0
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        for pattern in syslog_patterns:
            if re.search(pattern, line):
                matching_lines += 1
                break
    
    return matching_lines >= max(1, len([l for l in lines if l.strip()]) // 2)


def ensure_upload_dir():
    """Ensure upload directory exists"""
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)


def clean_old_files(max_age_hours: int = 24):
    """Clean old uploaded files"""
    import time
    
    if not os.path.exists(settings.UPLOAD_DIR):
        return
    
    current_time = time.time()
    max_age_seconds = max_age_hours * 3600
    
    for filename in os.listdir(settings.UPLOAD_DIR):
        filepath = os.path.join(settings.UPLOAD_DIR, filename)
        if os.path.isfile(filepath):
            file_age = current_time - os.path.getctime(filepath)
            if file_age > max_age_seconds:
                try:
                    os.remove(filepath)
                except OSError:
                    pass  # File might be in use


def get_file_path(file_id: str) -> Optional[str]:
    """Get file path for a given file ID"""
    if not os.path.exists(settings.UPLOAD_DIR):
        return None
    
    for filename in os.listdir(settings.UPLOAD_DIR):
        if filename.startswith(f"{file_id}_"):
            return os.path.join(settings.UPLOAD_DIR, filename)
    
    return None
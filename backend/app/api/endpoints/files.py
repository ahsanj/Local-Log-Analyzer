from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from typing import List
import os
import uuid
from datetime import datetime

from app.models.schemas import FileUploadResponse, FileInfo, LogFormat
from app.core.config import settings
from app.services.file_processor import FileProcessor
from app.services.chat_service import ChatService
from app.utils.file_utils import get_file_format, validate_file_size

router = APIRouter()
file_processor = FileProcessor()
chat_service = ChatService()


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """Upload a log file for analysis"""
    
    # Validate file extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"File type {file_ext} not supported. Allowed types: {settings.ALLOWED_EXTENSIONS}"
        )
    
    # Validate file size
    file_content = await file.read()
    if not validate_file_size(len(file_content)):
        raise HTTPException(
            status_code=400, 
            detail=f"File size exceeds maximum limit of {settings.MAX_FILE_SIZE / 1024 / 1024}MB"
        )
    
    # Generate unique file ID
    file_id = str(uuid.uuid4())
    
    # Create uploads directory if it doesn't exist
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    # Save file
    file_path = os.path.join(settings.UPLOAD_DIR, f"{file_id}_{file.filename}")
    with open(file_path, "wb") as buffer:
        buffer.write(file_content)
    
    # Detect file format
    file_format = get_file_format(file_content, file.filename)
    
    # Automatically create session context for immediate analysis
    try:
        await _create_session_context(file_id, file_path)
    except Exception as e:
        print(f"Warning: Failed to create session context for {file_id}: {e}")
    
    return FileUploadResponse(
        id=file_id,
        filename=file.filename,
        size=len(file_content),
        format=file_format,
        upload_time=datetime.now(),
        status="uploaded"
    )


@router.post("/paste", response_model=FileUploadResponse)
async def paste_content(content: dict):
    """Process pasted log content"""
    
    text_content = content.get("content", "")
    if not text_content:
        raise HTTPException(status_code=400, detail="No content provided")
    
    # Validate content size
    content_bytes = text_content.encode('utf-8')
    if not validate_file_size(len(content_bytes)):
        raise HTTPException(
            status_code=400, 
            detail=f"Content size exceeds maximum limit of {settings.MAX_FILE_SIZE / 1024 / 1024}MB"
        )
    
    # Generate unique file ID
    file_id = str(uuid.uuid4())
    
    # Create uploads directory if it doesn't exist
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    # Save content as file
    filename = f"pasted_content_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    file_path = os.path.join(settings.UPLOAD_DIR, f"{file_id}_{filename}")
    with open(file_path, "w", encoding='utf-8') as buffer:
        buffer.write(text_content)
    
    # Detect file format
    file_format = get_file_format(content_bytes, filename)
    
    # Automatically create session context for immediate analysis
    try:
        await _create_session_context(file_id, file_path)
    except Exception as e:
        print(f"Warning: Failed to create session context for {file_id}: {e}")
    
    return FileUploadResponse(
        id=file_id,
        filename=filename,
        size=len(content_bytes),
        format=file_format,
        upload_time=datetime.now(),
        status="uploaded"
    )


@router.get("/", response_model=List[FileInfo])
async def list_files():
    """Get list of uploaded files"""
    files = []
    
    if not os.path.exists(settings.UPLOAD_DIR):
        return files
    
    for filename in os.listdir(settings.UPLOAD_DIR):
        if "_" in filename:
            try:
                file_id = filename.split("_", 1)[0]
                original_filename = filename.split("_", 1)[1]
                file_path = os.path.join(settings.UPLOAD_DIR, filename)
                stat = os.stat(file_path)
                
                # Read small sample to detect format
                with open(file_path, "rb") as f:
                    sample = f.read(1024)
                
                files.append(FileInfo(
                    id=file_id,
                    filename=original_filename,
                    size=stat.st_size,
                    format=get_file_format(sample, original_filename),
                    upload_time=datetime.fromtimestamp(stat.st_ctime),
                    status="ready"
                ))
            except Exception:
                continue  # Skip malformed files
    
    return sorted(files, key=lambda x: x.upload_time, reverse=True)


@router.get("/{file_id}", response_model=FileInfo)
async def get_file_info(file_id: str):
    """Get information about a specific file"""
    
    # Find file with this ID
    if not os.path.exists(settings.UPLOAD_DIR):
        raise HTTPException(status_code=404, detail="File not found")
    
    for filename in os.listdir(settings.UPLOAD_DIR):
        if filename.startswith(f"{file_id}_"):
            file_path = os.path.join(settings.UPLOAD_DIR, filename)
            original_filename = filename.split("_", 1)[1]
            stat = os.stat(file_path)
            
            # Read small sample to detect format
            with open(file_path, "rb") as f:
                sample = f.read(1024)
            
            return FileInfo(
                id=file_id,
                filename=original_filename,
                size=stat.st_size,
                format=get_file_format(sample, original_filename),
                upload_time=datetime.fromtimestamp(stat.st_ctime),
                status="ready"
            )
    
    raise HTTPException(status_code=404, detail="File not found")


@router.delete("/{file_id}")
async def delete_file(file_id: str):
    """Delete a file"""
    
    if not os.path.exists(settings.UPLOAD_DIR):
        raise HTTPException(status_code=404, detail="File not found")
    
    for filename in os.listdir(settings.UPLOAD_DIR):
        if filename.startswith(f"{file_id}_"):
            file_path = os.path.join(settings.UPLOAD_DIR, filename)
            os.remove(file_path)
            return {"message": "File deleted successfully"}
    
    raise HTTPException(status_code=404, detail="File not found")


async def _create_session_context(file_id: str, file_path: str):
    """Automatically create session context when file is uploaded"""
    
    try:
        # Read and process the file
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Process the file to get log entries
        entries, detected_format = await file_processor.process_content(content, os.path.basename(file_path))
        
        if not entries:
            return  # No entries to analyze
        
        # Build detailed context similar to chat endpoint
        total_entries = len(entries)
        level_distribution = {}
        services = {}
        error_entries = []
        warning_entries = []
        
        for entry in entries:
            # Level distribution
            if entry.level:
                level_key = str(entry.level)
                level_distribution[level_key] = level_distribution.get(level_key, 0) + 1
            
            # Service distribution
            if entry.service:
                services[entry.service] = services.get(entry.service, 0) + 1
            
            # Collect errors and warnings
            if entry.level and "ERROR" in str(entry.level):
                error_entries.append({
                    "timestamp": str(entry.timestamp) if entry.timestamp else "unknown",
                    "service": entry.service or "unknown",
                    "message": entry.message,
                    "raw_line": entry.raw_line
                })
            elif entry.level and "WARN" in str(entry.level):
                warning_entries.append({
                    "timestamp": str(entry.timestamp) if entry.timestamp else "unknown", 
                    "service": entry.service or "unknown",
                    "message": entry.message,
                    "raw_line": entry.raw_line
                })
        
        # Get date range
        timestamps = [entry.timestamp for entry in entries if entry.timestamp]
        date_range = {}
        if timestamps:
            date_range = {
                "start": str(min(timestamps)),
                "end": str(max(timestamps))
            }
        
        # Sample entries
        sample_entries = []
        for entry in entries[:10]:
            sample_entries.append({
                "timestamp": str(entry.timestamp) if entry.timestamp else "unknown",
                "level": str(entry.level) if entry.level else "unknown",
                "service": entry.service or "unknown",
                "message": entry.message
            })
        
        # Create the session context
        file_context = {
            "total_entries": total_entries,
            "date_range": date_range,
            "level_distribution": level_distribution,
            "services": services,
            "error_entries": error_entries[:10],  # Top 10 errors
            "warning_entries": warning_entries[:10],  # Top 10 warnings 
            "sample_entries": sample_entries,
            "format": detected_format.value if detected_format else "unknown",
            "file_id": file_id,
            "processed_at": str(datetime.now())
        }
        
        # Store in session (use file_id as session_id)
        await chat_service.set_file_context(file_id, file_context)
        
        print(f" Session context created for file {file_id}: {total_entries} entries, {len(error_entries)} errors")
        
    except Exception as e:
        print(f" Failed to create session context for {file_id}: {e}")
        raise
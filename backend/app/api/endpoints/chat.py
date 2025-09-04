from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import os

from app.models.schemas import ChatRequest, ChatResponse, ChatMessage
from app.core.config import settings
from app.services.chat_service import ChatService

router = APIRouter()
chat_service = ChatService()


@router.post("/", response_model=ChatResponse)
async def chat_with_logs(request: ChatRequest):
    """Send a chat message and get AI response about logs with session persistence"""
    
    try:
        print(f"🗣️ Chat request: file_id={request.file_id}, session_id={request.session_id}, message='{request.message[:50]}...'")
        
        # Get file context if file_id provided
        file_context = None
        if request.file_id:
            file_context = await get_enhanced_file_context(request.file_id)
            print(f" File context loaded: {file_context.get('total_entries', 0) if file_context else 0} entries")
        
        # Use file_id as session_id if provided, otherwise use request.session_id
        session_id = request.file_id if request.file_id else request.session_id
        print(f"🔑 Using session_id: {session_id}")
        
        # Use session-based response generation for persistence
        response = await chat_service.generate_session_response(
            session_id=session_id,
            message=request.message,
            file_context=file_context
        )
        
        print(f" Chat response generated: {len(response.context)} messages in context")
        return response
    except Exception as e:
        print(f" Chat error: {e}")
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


@router.get("/history/{session_id}", response_model=List[ChatMessage])
async def get_chat_history(session_id: str):
    """Get chat history for a session"""
    
    print(f"📜 GET Chat history request for session_id: {session_id}")
    
    try:
        history = await chat_service.get_chat_history(session_id)
        print(f" Found {len(history)} messages in history")
        return history
    except Exception as e:
        print(f" History retrieval error: {e}")
        raise HTTPException(status_code=500, detail=f"History retrieval failed: {str(e)}")


@router.get("/session/{file_id}")
async def get_complete_chat_session(file_id: str):
    """Get complete chat session for a file - alternative endpoint"""
    
    print(f" GET Complete chat session request for file_id: {file_id}")
    
    try:
        # Get chat history using file_id as session_id
        history = await chat_service.get_chat_history(file_id)
        
        # Get file context
        context = await chat_service.get_file_context(file_id)
        
        print(f" Session: {len(history)} messages, context: {bool(context)}")
        
        return {
            "file_id": file_id,
            "session_id": file_id,
            "chat_history": history,
            "has_context": bool(context and context.get("total_entries", 0) > 0),
            "total_entries": context.get("total_entries", 0) if context else 0
        }
        
    except Exception as e:
        print(f" Complete session retrieval error: {e}")
        raise HTTPException(status_code=500, detail=f"Complete session retrieval failed: {str(e)}")


@router.delete("/history/{session_id}")
async def clear_chat_history(session_id: str):
    """Clear chat history and context for a session"""
    
    try:
        await chat_service.clear_session(session_id)
        return {"message": "Session cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Session clearing failed: {str(e)}")


@router.get("/suggestions/{file_id}")
async def get_suggested_questions(file_id: str):
    """Get suggested questions for a log file"""
    
    try:
        file_context = await get_file_context(file_id)
        suggestions = await chat_service.generate_suggestions(file_context)
        return {"suggestions": suggestions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Suggestion generation failed: {str(e)}")


async def get_enhanced_file_context(file_id: str) -> Dict[str, Any]:
    """Get enhanced file context for chat with detailed log analysis"""
    
    # Find the file
    file_path = None
    if os.path.exists(settings.UPLOAD_DIR):
        for filename in os.listdir(settings.UPLOAD_DIR):
            if filename.startswith(f"{file_id}_"):
                file_path = os.path.join(settings.UPLOAD_DIR, filename)
                break
    
    if not file_path:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Process the file directly to get detailed context
    from app.services.file_processor import FileProcessor
    
    file_processor = FileProcessor()
    
    # Read and process the file
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    entries, detected_format = await file_processor.process_content(content, os.path.basename(file_path))
    
    # Build enhanced context
    if not entries:
        return {"total_entries": 0, "message": "No log entries found"}
    
    # Extract detailed metrics
    total_entries = len(entries)
    level_distribution = {}
    services = {}
    error_entries = []
    warning_entries = []
    sample_entries = []
    
    for entry in entries:
        # Level distribution
        if entry.level:
            level_key = str(entry.level)
            level_distribution[level_key] = level_distribution.get(level_key, 0) + 1
        
        # Service distribution
        if entry.service:
            services[entry.service] = services.get(entry.service, 0) + 1
        
        # Collect error entries with full details
        if entry.level and "ERROR" in str(entry.level):
            error_entries.append({
                "timestamp": str(entry.timestamp) if entry.timestamp else "unknown",
                "service": entry.service or "unknown",
                "message": entry.message,
                "raw_line": entry.raw_line
            })
        
        # Collect warning entries
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
    
    # Sample entries (mix of different types)
    sample_entries = []
    for entry in entries[:10]:  # First 10 entries
        sample_entries.append({
            "timestamp": str(entry.timestamp) if entry.timestamp else "unknown",
            "level": str(entry.level) if entry.level else "unknown",
            "service": entry.service or "unknown",
            "message": entry.message
        })
    
    return {
        "total_entries": total_entries,
        "date_range": date_range,
        "level_distribution": level_distribution,
        "services": services,
        "error_entries": error_entries[:10],  # Top 10 errors
        "warning_entries": warning_entries[:10],  # Top 10 warnings
        "sample_entries": sample_entries,
        "format": detected_format.value if detected_format else "unknown"
    }

async def get_file_context(file_id: str) -> Dict[str, Any]:
    """Legacy function - redirects to enhanced version"""
    return await get_enhanced_file_context(file_id)
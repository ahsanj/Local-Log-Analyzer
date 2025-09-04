from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Dict, Any
import os

from app.models.schemas import LogAnalysis, PatternMatch, AnalysisRequest
from app.core.config import settings
from app.services.log_analyzer import LogAnalyzer
from app.services.pattern_detector import PatternDetector
from app.services.chat_service import ChatService

router = APIRouter()
log_analyzer = LogAnalyzer()
pattern_detector = PatternDetector()
chat_service = ChatService()


@router.get("/{file_id}", response_model=LogAnalysis)
async def get_analysis(file_id: str):
    """Get existing analysis results from persistent context"""
    
    print(f"📊 GET Analysis request for file_id: {file_id}")
    
    # Check if we have persistent context
    context = await chat_service.get_file_context(file_id)
    
    if context and context.get("total_entries", 0) > 0:
        print(f" Context found: {context.get('total_entries', 0)} entries")
        # Use persistent context to build analysis result
        analysis = _build_analysis_from_context(context)
        return analysis
    
    print(f" No context found for file_id: {file_id}")
    # If no persistent context, return empty analysis
    raise HTTPException(status_code=404, detail="No analysis data available")


@router.get("/{file_id}/session")
async def get_analysis_session(file_id: str):
    """Get full analysis session including chat history and analysis data"""
    
    print(f" GET Analysis session request for file_id: {file_id}")
    
    try:
        # Get file context
        context = await chat_service.get_file_context(file_id)
        print(f" Context: {context.get('total_entries', 0) if context else 0} entries")
        
        # Get chat history
        chat_history = await chat_service.get_chat_history(file_id)
        print(f" Chat history: {len(chat_history)} messages")
        
        # Build analysis if context exists
        analysis = None
        if context and context.get("total_entries", 0) > 0:
            analysis = _build_analysis_from_context(context)
            print(f" Analysis built successfully")
        else:
            print(f" No analysis context available")
        
        return {
            "analysis": analysis,
            "chat_history": chat_history,
            "context_exists": bool(context and context.get("total_entries", 0) > 0),
            "file_id": file_id
        }
        
    except Exception as e:
        print(f" Session retrieval error: {e}")
        raise HTTPException(status_code=500, detail=f"Session retrieval failed: {str(e)}")


@router.post("/{file_id}", response_model=LogAnalysis) 
async def analyze_file(file_id: str, request: AnalysisRequest = None):
    """Analyze a log file and return analysis results with persistent context"""
    
    # Check if we have persistent context first
    context = await chat_service.get_file_context(file_id)
    
    if context and context.get("total_entries", 0) > 0:
        # Use persistent context to build analysis result
        analysis = _build_analysis_from_context(context)
        return analysis
    
    # Fallback to traditional analysis if no persistent context
    # Find the file
    file_path = None
    if os.path.exists(settings.UPLOAD_DIR):
        for filename in os.listdir(settings.UPLOAD_DIR):
            if filename.startswith(f"{file_id}_"):
                file_path = os.path.join(settings.UPLOAD_DIR, filename)
                break
    
    if not file_path:
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        # Perform log analysis
        analysis = await log_analyzer.analyze_file(file_path)
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/{file_id}/patterns", response_model=List[PatternMatch])
async def get_patterns(file_id: str):
    """Get detected patterns for a file"""
    
    # Find the file
    file_path = None
    if os.path.exists(settings.UPLOAD_DIR):
        for filename in os.listdir(settings.UPLOAD_DIR):
            if filename.startswith(f"{file_id}_"):
                file_path = os.path.join(settings.UPLOAD_DIR, filename)
                break
    
    if not file_path:
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        # Detect patterns
        patterns = await pattern_detector.detect_patterns(file_path)
        return patterns
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pattern detection failed: {str(e)}")


@router.get("/{file_id}/stats")
async def get_file_stats(file_id: str):
    """Get basic statistics for a file"""
    
    # Find the file
    file_path = None
    if os.path.exists(settings.UPLOAD_DIR):
        for filename in os.listdir(settings.UPLOAD_DIR):
            if filename.startswith(f"{file_id}_"):
                file_path = os.path.join(settings.UPLOAD_DIR, filename)
                break
    
    if not file_path:
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        # Get basic stats
        stats = await log_analyzer.get_basic_stats(file_path)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats generation failed: {str(e)}")


@router.get("/{file_id}/entries")
async def get_log_entries(
    file_id: str, 
    offset: int = 0, 
    limit: int = 100,
    level: str = None,
    service: str = None,
    search: str = None
):
    """Get log entries with filtering and pagination"""
    
    # Find the file
    file_path = None
    if os.path.exists(settings.UPLOAD_DIR):
        for filename in os.listdir(settings.UPLOAD_DIR):
            if filename.startswith(f"{file_id}_"):
                file_path = os.path.join(settings.UPLOAD_DIR, filename)
                break
    
    if not file_path:
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        # Get filtered entries
        entries = await log_analyzer.get_entries(
            file_path, 
            offset=offset, 
            limit=limit,
            level_filter=level,
            service_filter=service,
            search_term=search
        )
        return entries
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Entry retrieval failed: {str(e)}")


@router.get("/{file_id}/timeline")
async def get_timeline_data(file_id: str, interval: str = "1h"):
    """Get timeline data for visualization"""
    
    # Find the file
    file_path = None
    if os.path.exists(settings.UPLOAD_DIR):
        for filename in os.listdir(settings.UPLOAD_DIR):
            if filename.startswith(f"{file_id}_"):
                file_path = os.path.join(settings.UPLOAD_DIR, filename)
                break
    
    if not file_path:
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        # Get timeline data
        timeline = await log_analyzer.get_timeline_data(file_path, interval)
        return timeline
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Timeline generation failed: {str(e)}")


def _build_analysis_from_context(context: Dict[str, Any]) -> LogAnalysis:
    """Build LogAnalysis object from persistent session context"""
    
    from datetime import datetime
    from app.models.schemas import LogLevel
    
    # Extract date range as dict with start/end datetime objects
    date_range_data = context.get("date_range", {})
    date_range = {"start": None, "end": None}
    if date_range_data and date_range_data.get("start") and date_range_data.get("end"):
        try:
            start_str = date_range_data["start"]
            end_str = date_range_data["end"]
            # Handle different datetime formats
            if "Z" in start_str:
                start_str = start_str.replace("Z", "+00:00")
            if "Z" in end_str:
                end_str = end_str.replace("Z", "+00:00")
            start = datetime.fromisoformat(start_str)
            end = datetime.fromisoformat(end_str)
            date_range = {"start": start, "end": end}
        except Exception as e:
            print(f"Warning: Failed to parse date range: {e}")
            date_range = {"start": None, "end": None}
    
    # Convert level distribution to use LogLevel enum
    level_distribution = {}
    for level_str, count in context.get("level_distribution", {}).items():
        # Extract enum value from string like "LogLevel.ERROR"
        if "." in level_str:
            level_key = level_str.split(".")[-1]
        else:
            level_key = level_str
        
        # Convert to LogLevel enum
        try:
            log_level = LogLevel(level_key.upper())
            level_distribution[log_level] = count
        except ValueError:
            # Fallback for unknown levels
            level_distribution[level_str] = count
    
    # Get service distribution
    service_distribution = context.get("services", {})
    
    # Create error patterns as List[Dict[str, Any]]
    error_patterns = []
    for error in context.get("error_entries", [])[:5]:
        error_patterns.append({
            "pattern": f"{error.get('service', 'unknown')}: {error.get('message', '')[:100]}",
            "service": error.get('service', 'unknown'),
            "count": 1,
            "severity": "high"
        })
    
    # Create anomalies as List[Dict[str, Any]]
    anomalies = []
    error_count = sum(count for level, count in level_distribution.items() if "ERROR" in str(level))
    if error_count > 10:
        anomalies.append({
            "type": "high_error_rate",
            "description": f"High error rate detected: {error_count} errors",
            "severity": "high",
            "count": error_count
        })
    
    warn_count = sum(count for level, count in level_distribution.items() if "WARN" in str(level))
    if warn_count > 20:
        anomalies.append({
            "type": "high_warning_rate", 
            "description": f"High warning rate detected: {warn_count} warnings",
            "severity": "medium",
            "count": warn_count
        })
    
    # Create time series data (simplified)
    time_series = [{
        "timestamp": datetime.now().isoformat(),
        "error_count": error_count,
        "warn_count": warn_count,
        "info_count": sum(count for level, count in level_distribution.items() if "INFO" in str(level)),
        "total_count": context.get("total_entries", 0)
    }]
    
    return LogAnalysis(
        total_entries=context.get("total_entries", 0),
        date_range=date_range,
        level_distribution=level_distribution, 
        service_distribution=service_distribution,
        error_patterns=error_patterns,
        anomalies=anomalies,
        time_series=time_series
    )
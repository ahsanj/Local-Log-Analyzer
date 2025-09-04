from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import re
import pandas as pd
from app.models.schemas import LogEntry, LogAnalysis, LogLevel, TimeSeriesData
from app.services.file_processor import FileProcessor
from app.core.config import settings


class LogAnalyzer:
    """Analyze log entries and generate insights"""
    
    def __init__(self):
        self.file_processor = FileProcessor()
    
    async def analyze_file(self, file_path: str) -> LogAnalysis:
        """Perform comprehensive analysis of a log file"""
        
        # Process the file to get log entries
        entries = await self.file_processor.process_file(file_path)
        
        if not entries:
            return LogAnalysis(
                total_entries=0,
                date_range={"start": None, "end": None},
                level_distribution={},
                service_distribution={},
                error_patterns=[],
                anomalies=[],
                time_series=[]
            )
        
        # Basic statistics
        total_entries = len(entries)
        date_range = self._get_date_range(entries)
        level_distribution = self._get_level_distribution(entries)
        service_distribution = self._get_service_distribution(entries)
        
        # Pattern detection
        error_patterns = await self._detect_error_patterns(entries)
        
        # Anomaly detection
        anomalies = await self._detect_anomalies(entries)
        
        # Time series data
        time_series = await self._generate_time_series(entries)
        
        return LogAnalysis(
            total_entries=total_entries,
            date_range=date_range,
            level_distribution=level_distribution,
            service_distribution=service_distribution,
            error_patterns=error_patterns,
            anomalies=anomalies,
            time_series=time_series
        )
    
    async def get_basic_stats(self, file_path: str) -> Dict[str, Any]:
        """Get basic statistics for a file"""
        
        entries = await self.file_processor.process_file(file_path)
        
        return {
            "total_entries": len(entries),
            "date_range": self._get_date_range(entries),
            "level_counts": self._get_level_distribution(entries),
            "service_counts": self._get_service_distribution(entries),
            "has_timestamps": sum(1 for e in entries if e.timestamp) > 0,
            "has_services": sum(1 for e in entries if e.service) > 0,
        }
    
    async def get_entries(
        self,
        file_path: str,
        offset: int = 0,
        limit: int = 100,
        level_filter: Optional[str] = None,
        service_filter: Optional[str] = None,
        search_term: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get filtered log entries with pagination"""
        
        entries = await self.file_processor.process_file(file_path)
        
        # Apply filters
        filtered_entries = []
        for entry in entries:
            # Level filter
            if level_filter and (not entry.level or entry.level.value != level_filter):
                continue
            
            # Service filter
            if service_filter and (not entry.service or entry.service != service_filter):
                continue
            
            # Search filter
            if search_term and search_term.lower() not in entry.message.lower():
                continue
            
            filtered_entries.append(entry)
        
        # Pagination
        total = len(filtered_entries)
        paginated_entries = filtered_entries[offset:offset + limit]
        
        return {
            "entries": [self._entry_to_dict(entry) for entry in paginated_entries],
            "total": total,
            "offset": offset,
            "limit": limit
        }
    
    async def get_timeline_data(self, file_path: str, interval: str = "1h") -> List[Dict[str, Any]]:
        """Generate timeline data for visualization"""
        
        entries = await self.file_processor.process_file(file_path)
        
        # Filter entries with timestamps
        timestamped_entries = [e for e in entries if e.timestamp]
        
        if not timestamped_entries:
            return []
        
        # Group by time interval
        interval_minutes = self._parse_interval(interval)
        grouped_data = defaultdict(lambda: {"error": 0, "warn": 0, "info": 0, "other": 0, "total": 0})
        
        for entry in timestamped_entries:
            # Round timestamp to interval
            rounded_time = self._round_timestamp(entry.timestamp, interval_minutes)
            key = rounded_time.isoformat()
            
            # Count by level
            if entry.level in [LogLevel.ERROR, LogLevel.FATAL, LogLevel.CRITICAL]:
                grouped_data[key]["error"] += 1
            elif entry.level in [LogLevel.WARN, LogLevel.WARNING]:
                grouped_data[key]["warn"] += 1
            elif entry.level == LogLevel.INFO:
                grouped_data[key]["info"] += 1
            else:
                grouped_data[key]["other"] += 1
            
            grouped_data[key]["total"] += 1
        
        # Convert to list and sort by time
        timeline_data = []
        for timestamp_str, counts in grouped_data.items():
            timeline_data.append({
                "timestamp": timestamp_str,
                "error_count": counts["error"],
                "warn_count": counts["warn"],
                "info_count": counts["info"],
                "other_count": counts["other"],
                "total_count": counts["total"]
            })
        
        return sorted(timeline_data, key=lambda x: x["timestamp"])
    
    async def get_file_context_for_chat(self, file_path: str) -> Dict[str, Any]:
        """Get file context for chat functionality"""
        
        entries = await self.file_processor.process_file(file_path)
        
        # Sample entries for context
        sample_entries = entries[:10] if len(entries) > 10 else entries
        
        # Error examples
        error_entries = [e for e in entries if e.level in [LogLevel.ERROR, LogLevel.FATAL, LogLevel.CRITICAL]][:5]
        
        # Service breakdown
        services = self._get_service_distribution(entries)
        
        return {
            "total_entries": len(entries),
            "sample_entries": [self._entry_to_dict(entry) for entry in sample_entries],
            "error_entries": [self._entry_to_dict(entry) for entry in error_entries],
            "services": dict(list(services.items())[:10]),  # Top 10 services
            "date_range": self._get_date_range(entries),
            "level_distribution": self._get_level_distribution(entries)
        }
    
    def _get_date_range(self, entries: List[LogEntry]) -> Dict[str, Optional[datetime]]:
        """Get date range from entries"""
        timestamped_entries = [e for e in entries if e.timestamp]
        
        if not timestamped_entries:
            return {"start": None, "end": None}
        
        timestamps = [e.timestamp for e in timestamped_entries]
        return {
            "start": min(timestamps),
            "end": max(timestamps)
        }
    
    def _get_level_distribution(self, entries: List[LogEntry]) -> Dict[LogLevel, int]:
        """Get distribution of log levels"""
        distribution = defaultdict(int)
        
        for entry in entries:
            if entry.level:
                distribution[entry.level] += 1
            else:
                distribution[LogLevel.INFO] += 1  # Default for unknown levels
        
        return dict(distribution)
    
    def _get_service_distribution(self, entries: List[LogEntry]) -> Dict[str, int]:
        """Get distribution of services/components"""
        distribution = defaultdict(int)
        
        for entry in entries:
            service = entry.service or "unknown"
            distribution[service] += 1
        
        # Sort by count and return top services
        sorted_services = sorted(distribution.items(), key=lambda x: x[1], reverse=True)
        return dict(sorted_services[:20])  # Top 20 services
    
    async def _detect_error_patterns(self, entries: List[LogEntry]) -> List[Dict[str, Any]]:
        """Detect common error patterns"""
        
        error_entries = [e for e in entries if e.level in [LogLevel.ERROR, LogLevel.FATAL, LogLevel.CRITICAL]]
        
        if not error_entries:
            return []
        
        # Group similar error messages
        error_patterns = defaultdict(list)
        
        for entry in error_entries:
            # Normalize the error message to detect patterns
            normalized = self._normalize_error_message(entry.message)
            error_patterns[normalized].append(entry)
        
        # Convert to pattern matches
        patterns = []
        for pattern, matching_entries in error_patterns.items():
            if len(matching_entries) >= 2:  # Only patterns that occur multiple times
                patterns.append({
                    "pattern": pattern,
                    "count": len(matching_entries),
                    "examples": [e.message for e in matching_entries[:3]],
                    "severity": "high" if len(matching_entries) > 10 else "medium",
                    "category": "error",
                    "first_occurrence": min(e.timestamp for e in matching_entries if e.timestamp),
                    "last_occurrence": max(e.timestamp for e in matching_entries if e.timestamp),
                })
        
        return sorted(patterns, key=lambda x: x["count"], reverse=True)[:10]
    
    async def _detect_anomalies(self, entries: List[LogEntry]) -> List[Dict[str, Any]]:
        """Detect anomalies in the log data"""
        
        anomalies = []
        
        # Time-based anomaly detection
        if len(entries) > 100:
            time_anomalies = await self._detect_time_anomalies(entries)
            anomalies.extend(time_anomalies)
        
        # Volume anomaly detection
        volume_anomalies = await self._detect_volume_anomalies(entries)
        anomalies.extend(volume_anomalies)
        
        # Error spike detection
        error_anomalies = await self._detect_error_spikes(entries)
        anomalies.extend(error_anomalies)
        
        return anomalies[:10]  # Limit to top 10 anomalies
    
    async def _detect_time_anomalies(self, entries: List[LogEntry]) -> List[Dict[str, Any]]:
        """Detect time-based anomalies (gaps, bursts)"""
        
        timestamped_entries = sorted([e for e in entries if e.timestamp], key=lambda x: x.timestamp)
        
        if len(timestamped_entries) < 10:
            return []
        
        anomalies = []
        
        # Detect large gaps in logging
        time_gaps = []
        for i in range(1, len(timestamped_entries)):
            gap = (timestamped_entries[i].timestamp - timestamped_entries[i-1].timestamp).total_seconds()
            time_gaps.append(gap)
        
        if time_gaps:
            avg_gap = sum(time_gaps) / len(time_gaps)
            threshold = avg_gap * 10  # 10x average gap
            
            for i, gap in enumerate(time_gaps):
                if gap > threshold and gap > 300:  # At least 5 minutes
                    anomalies.append({
                        "type": "time_gap",
                        "description": f"Large gap in logging: {gap/60:.1f} minutes",
                        "timestamp": timestamped_entries[i].timestamp.isoformat(),
                        "severity": "medium",
                        "affected_entries": 0
                    })
        
        return anomalies
    
    async def _detect_volume_anomalies(self, entries: List[LogEntry]) -> List[Dict[str, Any]]:
        """Detect volume anomalies (unusual log volumes)"""
        
        anomalies = []
        
        # Group by hour
        hourly_counts = defaultdict(int)
        for entry in entries:
            if entry.timestamp:
                hour_key = entry.timestamp.replace(minute=0, second=0, microsecond=0)
                hourly_counts[hour_key] += 1
        
        if len(hourly_counts) < 3:
            return anomalies
        
        counts = list(hourly_counts.values())
        avg_count = sum(counts) / len(counts)
        
        # Detect hours with unusually high volume (3x average)
        for hour, count in hourly_counts.items():
            if count > avg_count * 3 and count > 100:
                anomalies.append({
                    "type": "volume_spike",
                    "description": f"Unusual high log volume: {count} entries in 1 hour",
                    "timestamp": hour.isoformat(),
                    "severity": "medium" if count > avg_count * 5 else "low",
                    "affected_entries": count
                })
        
        return anomalies
    
    async def _detect_error_spikes(self, entries: List[LogEntry]) -> List[Dict[str, Any]]:
        """Detect error spikes"""
        
        error_entries = [e for e in entries if e.level in [LogLevel.ERROR, LogLevel.FATAL, LogLevel.CRITICAL] and e.timestamp]
        
        if len(error_entries) < 10:
            return []
        
        # Group errors by 10-minute intervals
        interval_errors = defaultdict(int)
        for entry in error_entries:
            interval_key = entry.timestamp.replace(minute=(entry.timestamp.minute // 10) * 10, second=0, microsecond=0)
            interval_errors[interval_key] += 1
        
        if len(interval_errors) < 3:
            return []
        
        error_counts = list(interval_errors.values())
        avg_errors = sum(error_counts) / len(error_counts)
        
        anomalies = []
        for interval, count in interval_errors.items():
            if count > avg_errors * 3 and count > 10:
                anomalies.append({
                    "type": "error_spike",
                    "description": f"Error spike: {count} errors in 10 minutes",
                    "timestamp": interval.isoformat(),
                    "severity": "high" if count > avg_errors * 5 else "medium",
                    "affected_entries": count
                })
        
        return anomalies
    
    async def _generate_time_series(self, entries: List[LogEntry]) -> List[TimeSeriesData]:
        """Generate time series data for visualization"""
        
        timestamped_entries = [e for e in entries if e.timestamp]
        
        if not timestamped_entries:
            return []
        
        # Group by hour
        hourly_data = defaultdict(lambda: {"error": 0, "warn": 0, "info": 0, "total": 0})
        
        for entry in timestamped_entries:
            hour_key = entry.timestamp.replace(minute=0, second=0, microsecond=0)
            
            if entry.level in [LogLevel.ERROR, LogLevel.FATAL, LogLevel.CRITICAL]:
                hourly_data[hour_key]["error"] += 1
            elif entry.level in [LogLevel.WARN, LogLevel.WARNING]:
                hourly_data[hour_key]["warn"] += 1
            elif entry.level == LogLevel.INFO:
                hourly_data[hour_key]["info"] += 1
            
            hourly_data[hour_key]["total"] += 1
        
        # Convert to time series data
        time_series = []
        for timestamp, counts in hourly_data.items():
            time_series.append(TimeSeriesData(
                timestamp=timestamp.isoformat(),
                error_count=counts["error"],
                warn_count=counts["warn"],
                info_count=counts["info"],
                total_count=counts["total"]
            ))
        
        return sorted(time_series, key=lambda x: x.timestamp)
    
    def _normalize_error_message(self, message: str) -> str:
        """Normalize error message to detect patterns"""
        
        # Remove specific values that vary but keep the pattern
        normalized = message
        
        # Replace timestamps
        normalized = re.sub(r'\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:?\d{2})?', 'TIMESTAMP', normalized)
        
        # Replace IDs and UUIDs
        normalized = re.sub(r'\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b', 'UUID', normalized)
        normalized = re.sub(r'\b\d{6,}\b', 'ID', normalized)
        
        # Replace IP addresses
        normalized = re.sub(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', 'IP_ADDRESS', normalized)
        
        # Replace file paths
        normalized = re.sub(r'[/\\][^\s]+', 'FILE_PATH', normalized)
        
        # Replace numbers
        normalized = re.sub(r'\b\d+\b', 'NUMBER', normalized)
        
        return normalized
    
    def _parse_interval(self, interval: str) -> int:
        """Parse interval string to minutes"""
        interval_map = {
            "1m": 1,
            "5m": 5,
            "15m": 15,
            "30m": 30,
            "1h": 60,
            "2h": 120,
            "6h": 360,
            "12h": 720,
            "1d": 1440
        }
        return interval_map.get(interval, 60)
    
    def _round_timestamp(self, timestamp: datetime, interval_minutes: int) -> datetime:
        """Round timestamp to interval"""
        total_minutes = timestamp.hour * 60 + timestamp.minute
        rounded_minutes = (total_minutes // interval_minutes) * interval_minutes
        
        return timestamp.replace(
            hour=rounded_minutes // 60,
            minute=rounded_minutes % 60,
            second=0,
            microsecond=0
        )
    
    def _entry_to_dict(self, entry: LogEntry) -> Dict[str, Any]:
        """Convert LogEntry to dictionary"""
        return {
            "timestamp": entry.timestamp.isoformat() if entry.timestamp else None,
            "level": entry.level.value if entry.level else None,
            "service": entry.service,
            "message": entry.message,
            "line_number": entry.line_number,
            "metadata": entry.metadata
        }
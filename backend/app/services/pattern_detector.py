import re
from typing import List, Dict, Any
from collections import defaultdict, Counter
from app.models.schemas import PatternMatch, LogEntry
from app.services.file_processor import FileProcessor


class PatternDetector:
    """Detect patterns in log files"""
    
    def __init__(self):
        self.file_processor = FileProcessor()
        
        # Common error patterns
        self.error_patterns = {
            "connection_error": r"(?i)(connection|connect).*(failed|error|refused|timeout|denied)",
            "memory_error": r"(?i)(memory|heap|oom|out of memory).*(error|exception|full)",
            "permission_error": r"(?i)(permission|access).*(denied|forbidden|error)",
            "file_error": r"(?i)(file|directory).*(not found|missing|error|corrupt)",
            "network_error": r"(?i)(network|socket|tcp|udp).*(error|timeout|unreachable)",
            "database_error": r"(?i)(database|db|sql).*(error|exception|timeout|deadlock)",
            "authentication_error": r"(?i)(auth|login|credential).*(failed|error|invalid|denied)",
            "timeout_error": r"(?i)(timeout|timed out|deadline exceeded)",
            "null_pointer": r"(?i)(null|nil).*(pointer|reference|exception|error)",
            "serialization_error": r"(?i)(serialize|deserialize|json|xml).*(error|exception|failed)"
        }
    
    async def detect_patterns(self, file_path: str) -> List[PatternMatch]:
        """Detect patterns in a log file"""
        
        # Process the file to get log entries
        entries = await self.file_processor.process_file(file_path)
        
        patterns = []
        
        # Detect error patterns
        error_patterns = await self._detect_error_patterns(entries)
        patterns.extend(error_patterns)
        
        # Detect repetitive message patterns
        repetitive_patterns = await self._detect_repetitive_patterns(entries)
        patterns.extend(repetitive_patterns)
        
        # Detect service-specific patterns
        service_patterns = await self._detect_service_patterns(entries)
        patterns.extend(service_patterns)
        
        # Sort by count and return top patterns
        return sorted(patterns, key=lambda x: x.count, reverse=True)[:20]
    
    async def _detect_error_patterns(self, entries: List[LogEntry]) -> List[PatternMatch]:
        """Detect common error patterns"""
        
        patterns = []
        
        for pattern_name, pattern_regex in self.error_patterns.items():
            matching_entries = []
            
            for entry in entries:
                if re.search(pattern_regex, entry.message):
                    matching_entries.append(entry)
            
            if len(matching_entries) >= 2:  # Pattern must occur at least twice
                examples = [entry.message for entry in matching_entries[:3]]
                severity = self._calculate_severity(len(matching_entries), len(entries))
                
                first_occurrence = None
                last_occurrence = None
                if matching_entries:
                    timestamped_entries = [e for e in matching_entries if e.timestamp]
                    if timestamped_entries:
                        first_occurrence = min(e.timestamp for e in timestamped_entries)
                        last_occurrence = max(e.timestamp for e in timestamped_entries)
                
                patterns.append(PatternMatch(
                    pattern=pattern_name.replace("_", " ").title(),
                    count=len(matching_entries),
                    examples=examples,
                    severity=severity,
                    category="error",
                    first_occurrence=first_occurrence,
                    last_occurrence=last_occurrence
                ))
        
        return patterns
    
    async def _detect_repetitive_patterns(self, entries: List[LogEntry]) -> List[PatternMatch]:
        """Detect repetitive message patterns"""
        
        # Normalize messages to detect similar patterns
        normalized_messages = defaultdict(list)
        
        for entry in entries:
            normalized = self._normalize_message(entry.message)
            if len(normalized) > 10:  # Ignore very short messages
                normalized_messages[normalized].append(entry)
        
        patterns = []
        for normalized_msg, matching_entries in normalized_messages.items():
            if len(matching_entries) >= 5:  # Must repeat at least 5 times
                examples = [entry.message for entry in matching_entries[:3]]
                severity = self._calculate_severity(len(matching_entries), len(entries))
                
                first_occurrence = None
                last_occurrence = None
                if matching_entries:
                    timestamped_entries = [e for e in matching_entries if e.timestamp]
                    if timestamped_entries:
                        first_occurrence = min(e.timestamp for e in timestamped_entries)
                        last_occurrence = max(e.timestamp for e in timestamped_entries)
                
                # Determine category based on log level
                category = "info"
                if any(entry.level and "error" in entry.level.value.lower() for entry in matching_entries):
                    category = "error"
                elif any(entry.level and "warn" in entry.level.value.lower() for entry in matching_entries):
                    category = "warning"
                
                patterns.append(PatternMatch(
                    pattern=f"Repetitive: {self._truncate_message(examples[0])}",
                    count=len(matching_entries),
                    examples=examples,
                    severity=severity,
                    category=category,
                    first_occurrence=first_occurrence,
                    last_occurrence=last_occurrence
                ))
        
        return patterns
    
    async def _detect_service_patterns(self, entries: List[LogEntry]) -> List[PatternMatch]:
        """Detect service-specific patterns"""
        
        # Group entries by service
        service_entries = defaultdict(list)
        for entry in entries:
            if entry.service:
                service_entries[entry.service].append(entry)
        
        patterns = []
        for service, service_entries_list in service_entries.items():
            if len(service_entries_list) >= 10:  # Service must have enough entries
                
                # Find most common messages for this service
                message_counts = Counter(entry.message for entry in service_entries_list)
                
                for message, count in message_counts.most_common(5):
                    if count >= 3:  # Message must repeat at least 3 times
                        matching_entries = [e for e in service_entries_list if e.message == message]
                        severity = self._calculate_severity(count, len(service_entries_list))
                        
                        first_occurrence = None
                        last_occurrence = None
                        if matching_entries:
                            timestamped_entries = [e for e in matching_entries if e.timestamp]
                            if timestamped_entries:
                                first_occurrence = min(e.timestamp for e in timestamped_entries)
                                last_occurrence = max(e.timestamp for e in timestamped_entries)
                        
                        patterns.append(PatternMatch(
                            pattern=f"{service}: {self._truncate_message(message)}",
                            count=count,
                            examples=[message],
                            severity=severity,
                            category="service",
                            first_occurrence=first_occurrence,
                            last_occurrence=last_occurrence
                        ))
        
        return patterns
    
    def _normalize_message(self, message: str) -> str:
        """Normalize message to detect similar patterns"""
        
        normalized = message
        
        # Remove timestamps
        normalized = re.sub(r'\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:?\d{2})?', '<TIMESTAMP>', normalized)
        
        # Remove UUIDs
        normalized = re.sub(r'\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b', '<UUID>', normalized)
        
        # Remove long numbers (IDs, etc.)
        normalized = re.sub(r'\b\d{6,}\b', '<ID>', normalized)
        
        # Remove IP addresses
        normalized = re.sub(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '<IP>', normalized)
        
        # Remove URLs
        normalized = re.sub(r'https?://[^\s]+', '<URL>', normalized)
        
        # Remove file paths
        normalized = re.sub(r'[/\\][^\s]*[/\\][^\s]*', '<PATH>', normalized)
        
        # Remove quoted strings (but keep the quotes as pattern indicators)
        normalized = re.sub(r'"[^"]*"', '"<STRING>"', normalized)
        normalized = re.sub(r"'[^']*'", "'<STRING>'", normalized)
        
        # Remove numbers but keep their position
        normalized = re.sub(r'\b\d+\b', '<NUM>', normalized)
        
        # Normalize whitespace
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def _calculate_severity(self, pattern_count: int, total_entries: int) -> str:
        """Calculate pattern severity based on frequency"""
        
        frequency = pattern_count / total_entries if total_entries > 0 else 0
        
        if frequency > 0.1:  # More than 10% of all entries
            return "high"
        elif frequency > 0.05:  # More than 5% of all entries
            return "medium"
        else:
            return "low"
    
    def _truncate_message(self, message: str, max_length: int = 80) -> str:
        """Truncate message for display"""
        if len(message) <= max_length:
            return message
        return message[:max_length - 3] + "..."
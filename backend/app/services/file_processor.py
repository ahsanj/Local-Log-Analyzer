import os
import json
import csv
import re
from typing import List, Dict, Any, Optional, Tuple, Union
from datetime import datetime
from app.models.schemas import LogEntry, LogFormat, LogLevel
from app.utils.file_utils import get_file_format


class LogParsingError(Exception):
    """Custom exception for log parsing errors"""
    pass


class FileProcessor:
    """Advanced log file processor with intelligent format detection and parsing"""
    
    def __init__(self):
        # Comprehensive timestamp patterns with named groups
        self.timestamp_patterns = {
            'iso8601_with_tz': r'(?P<timestamp>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-]\d{2}:?\d{2})?)',
            'iso8601_simple': r'(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(?:\.\d{1,6})?)',
            'syslog': r'(?P<timestamp>\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})',
            'us_format': r'(?P<timestamp>\d{1,2}/\d{1,2}/\d{4} \d{2}:\d{2}:\d{2})',
            'european': r'(?P<timestamp>\d{1,2}\.\d{1,2}\.\d{4} \d{2}:\d{2}:\d{2})',
            'unix_timestamp': r'(?P<timestamp>\d{10}(?:\.\d{1,6})?)',
            'apache_common': r'(?P<timestamp>\d{2}/\w{3}/\d{4}:\d{2}:\d{2}:\d{2} [+-]\d{4})',
        }
        
        # Enhanced log level patterns with case variations
        self.log_level_patterns = {
            LogLevel.ERROR: [
                r'\b(?:ERROR|ERR|ERRO)\b',
                r'\b(?:error|err|erro)\b',
                r'\b(?:Error|Err|Erro)\b',
                r'\[(?:ERROR|ERR|ERRO)\]',
                r'\[(?:error|err|erro)\]',
            ],
            LogLevel.WARN: [
                r'\b(?:WARN|WARNING|WARN)\b',
                r'\b(?:warn|warning)\b',
                r'\b(?:Warn|Warning)\b',
                r'\[(?:WARN|WARNING)\]',
                r'\[(?:warn|warning)\]',
            ],
            LogLevel.INFO: [
                r'\b(?:INFO|INFORMATION)\b',
                r'\b(?:info|information)\b',
                r'\b(?:Info|Information)\b',
                r'\[(?:INFO|INFORMATION)\]',
                r'\[(?:info|information)\]',
            ],
            LogLevel.DEBUG: [
                r'\b(?:DEBUG|DBG)\b',
                r'\b(?:debug|dbg)\b',
                r'\b(?:Debug|Dbg)\b',
                r'\[(?:DEBUG|DBG)\]',
                r'\[(?:debug|dbg)\]',
            ],
            LogLevel.TRACE: [
                r'\b(?:TRACE|TRC)\b',
                r'\b(?:trace|trc)\b',
                r'\b(?:Trace|Trc)\b',
                r'\[(?:TRACE|TRC)\]',
                r'\[(?:trace|trc)\]',
            ],
            LogLevel.FATAL: [
                r'\b(?:FATAL|CRIT|CRITICAL)\b',
                r'\b(?:fatal|crit|critical)\b',
                r'\b(?:Fatal|Crit|Critical)\b',
                r'\[(?:FATAL|CRIT|CRITICAL)\]',
                r'\[(?:fatal|crit|critical)\]',
            ],
        }
        
        # Service/component extraction patterns
        self.service_patterns = [
            r'\[(?P<service>[^\]]+)\]',  # [service_name]
            r'(?P<service>\w+):\s',      # service_name: message
            r'\b(?P<service>\w+)\s*-\s', # service_name - message
            r'"service":\s*"(?P<service>[^"]+)"',  # JSON "service": "name"
            r'service=(?P<service>\w+)',  # key=value format
        ]
        
        # Format detection scoring thresholds
        self.detection_thresholds = {
            'json_confidence': 0.7,
            'csv_confidence': 0.8,
            'syslog_confidence': 0.6,
            'minimum_lines': 3,  # Minimum lines for reliable detection
        }
    
    async def process_file(self, file_path: str) -> List[LogEntry]:
        """Process a log file and return parsed entries with intelligent format detection"""
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            if not content.strip():
                raise LogParsingError("File is empty or contains only whitespace")
            
            # Intelligent format detection
            filename = os.path.basename(file_path)
            file_format, confidence = await self._detect_log_format(content, filename)
            
            print(f"Detected format: {file_format} (confidence: {confidence:.2f})")
            
            # Parse based on detected format
            if file_format == LogFormat.JSON:
                return await self._parse_json_logs(content)
            elif file_format == LogFormat.CSV:
                return await self._parse_csv_logs(content)
            elif file_format == LogFormat.SYSLOG:
                return await self._parse_syslog_logs(content)
            elif file_format == LogFormat.CUSTOM:
                return await self._parse_structured_logs(content)
            else:
                return await self._parse_plain_text_logs(content)
                
        except Exception as e:
            if isinstance(e, LogParsingError):
                raise
            raise LogParsingError(f"Failed to process file {filename}: {str(e)}")
    
    async def process_content(self, content: str, filename: str) -> Tuple[List[LogEntry], LogFormat]:
        """Process log content and return parsed entries with detected format"""
        
        if not content.strip():
            return [], LogFormat.PLAIN_TEXT
        
        # Intelligent format detection
        file_format, confidence = await self._detect_log_format(content, filename)
        
        print(f"Detected format: {file_format} (confidence: {confidence:.2f})")
        
        # Parse based on detected format
        if file_format == LogFormat.JSON:
            entries = await self._parse_json_logs(content)
        elif file_format == LogFormat.CSV:
            entries = await self._parse_csv_logs(content)
        elif file_format == LogFormat.SYSLOG:
            entries = await self._parse_syslog_logs(content)
        elif file_format == LogFormat.CUSTOM:
            entries = await self._parse_structured_logs(content)
        else:
            entries = await self._parse_plain_text_logs(content)
        
        return entries, file_format
    
    async def _detect_log_format(self, content: str, filename: str) -> Tuple[LogFormat, float]:
        """Intelligent log format detection with confidence scoring"""
        
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        if len(lines) < self.detection_thresholds['minimum_lines']:
            # Fallback to extension-based detection for very small files
            return self._format_from_extension(filename), 0.5
        
        # Take sample of lines for analysis (max 100 lines for performance)
        sample_lines = lines[:min(100, len(lines))]
        
        # Score each format
        json_score = self._score_json_format(sample_lines)
        csv_score = self._score_csv_format(sample_lines)
        syslog_score = self._score_syslog_format(sample_lines)
        structured_score = self._score_structured_format(sample_lines)
        
        scores = {
            LogFormat.JSON: json_score,
            LogFormat.CSV: csv_score,
            LogFormat.SYSLOG: syslog_score,
            LogFormat.CUSTOM: structured_score,
            LogFormat.PLAIN_TEXT: 0.1,  # Default fallback
        }
        
        # Find format with highest confidence
        best_format = max(scores, key=scores.get)
        confidence = scores[best_format]
        
        # Apply thresholds
        if best_format == LogFormat.JSON and confidence < self.detection_thresholds['json_confidence']:
            return LogFormat.PLAIN_TEXT, 0.5
        elif best_format == LogFormat.CSV and confidence < self.detection_thresholds['csv_confidence']:
            return LogFormat.PLAIN_TEXT, 0.5
        elif best_format == LogFormat.SYSLOG and confidence < self.detection_thresholds['syslog_confidence']:
            return LogFormat.PLAIN_TEXT, 0.5
            
        return best_format, confidence
    
    def _format_from_extension(self, filename: str) -> LogFormat:
        """Determine format from file extension"""
        ext = os.path.splitext(filename)[1].lower()
        extension_map = {
            '.json': LogFormat.JSON,
            '.csv': LogFormat.CSV,
            '.syslog': LogFormat.SYSLOG,
            '.log': LogFormat.PLAIN_TEXT,
            '.txt': LogFormat.PLAIN_TEXT,
        }
        return extension_map.get(ext, LogFormat.PLAIN_TEXT)
    
    def _score_json_format(self, lines: List[str]) -> float:
        """Score lines for JSON format likelihood"""
        if not lines:
            return 0.0
        
        valid_json_count = 0
        total_non_empty = len(lines)
        
        for line in lines:
            if not line.strip():
                total_non_empty -= 1
                continue
                
            try:
                parsed = json.loads(line)
                if isinstance(parsed, dict):
                    valid_json_count += 1
            except (json.JSONDecodeError, TypeError):
                continue
        
        if total_non_empty == 0:
            return 0.0
        
        return valid_json_count / total_non_empty
    
    def _score_csv_format(self, lines: List[str]) -> float:
        """Score lines for CSV format likelihood"""
        if len(lines) < 2:
            return 0.0
        
        try:
            # Try to detect CSV dialect
            sample = '\n'.join(lines[:10])
            sniffer = csv.Sniffer()
            dialect = sniffer.sniff(sample, delimiters=',;|\t')
            
            # Parse first few lines
            reader = csv.reader(lines[:5], dialect=dialect)
            rows = list(reader)
            
            if len(rows) < 2:
                return 0.0
            
            # Check for consistent column counts
            header_cols = len(rows[0])
            if header_cols < 2:  # CSV should have at least 2 columns
                return 0.0
            
            consistent_cols = sum(1 for row in rows[1:] if len(row) == header_cols)
            consistency_score = consistent_cols / (len(rows) - 1)
            
            # Bonus for header-like first row
            header_bonus = 0.2 if all(col.replace('_', '').replace(' ', '').isalpha() 
                                   for col in rows[0]) else 0
            
            return min(1.0, consistency_score + header_bonus)
            
        except Exception:
            return 0.0
    
    def _score_syslog_format(self, lines: List[str]) -> float:
        """Score lines for syslog format likelihood"""
        if not lines:
            return 0.0
        
        syslog_patterns = [
            r'^\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}',  # Standard syslog timestamp
            r'^<\d+>',  # Priority value
            r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}',  # ISO timestamp
        ]
        
        matching_lines = 0
        for line in lines[:20]:  # Check first 20 lines
            if any(re.search(pattern, line) for pattern in syslog_patterns):
                matching_lines += 1
        
        return matching_lines / min(len(lines), 20)
    
    def _score_structured_format(self, lines: List[str]) -> float:
        """Score lines for structured log format (key=value, etc.)"""
        if not lines:
            return 0.0
        
        structured_patterns = [
            r'\w+=\w+',  # key=value
            r'\w+:\s*\w+',  # key: value
            r'\[\w+\]',  # [component]
            r'\d{4}-\d{2}-\d{2}[\sT]\d{2}:\d{2}:\d{2}',  # timestamps
        ]
        
        structured_score = 0
        for line in lines[:20]:
            line_score = sum(1 for pattern in structured_patterns 
                           if re.search(pattern, line))
            structured_score += min(line_score / len(structured_patterns), 1.0)
        
        return structured_score / min(len(lines), 20)
    
    async def _parse_json_logs(self, content: str) -> List[LogEntry]:
        """Parse JSON format logs with robust error handling"""
        entries = []
        lines = content.strip().split('\n')
        successful_parses = 0
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
            
            try:
                data = json.loads(line)
                if isinstance(data, dict):
                    entry = await self._create_log_entry_from_json(data, line, line_num)
                    entries.append(entry)
                    successful_parses += 1
                else:
                    # Handle non-dict JSON (arrays, primitives)
                    entry = await self._create_fallback_entry(line, line_num, 
                                                            reason="Non-object JSON")
                    entries.append(entry)
            except json.JSONDecodeError as e:
                # Create fallback entry for malformed JSON
                entry = await self._create_fallback_entry(line, line_num, 
                                                        reason=f"JSON decode error: {str(e)}")
                entries.append(entry)
            except Exception as e:
                # Handle unexpected errors
                entry = await self._create_fallback_entry(line, line_num, 
                                                        reason=f"Unexpected error: {str(e)}")
                entries.append(entry)
        
        # Log parsing statistics
        total_lines = len([line for line in lines if line.strip()])
        if total_lines > 0:
            success_rate = successful_parses / total_lines
            print(f"JSON parsing success rate: {success_rate:.2%} ({successful_parses}/{total_lines})")
        
        return entries
    
    async def _parse_csv_logs(self, content: str) -> List[LogEntry]:
        """Parse CSV format logs with enhanced error handling"""
        entries = []
        successful_parses = 0
        
        try:
            # Detect CSV dialect with multiple delimiters
            lines = content.splitlines()
            if len(lines) < 2:
                raise LogParsingError("CSV file must have at least a header and one data row")
            
            sample = '\n'.join(lines[:min(10, len(lines))])
            sniffer = csv.Sniffer()
            
            # Try different delimiters if auto-detection fails
            delimiters = [',', ';', '\t', '|']
            dialect = None
            
            for delimiter in delimiters:
                try:
                    dialect = sniffer.sniff(sample, delimiters=delimiter)
                    break
                except csv.Error:
                    continue
            
            if dialect is None:
                # Fallback to comma delimiter
                dialect = csv.excel
            
            # Parse CSV with error handling for each row
            reader = csv.DictReader(lines, dialect=dialect)
            headers = reader.fieldnames
            
            if not headers:
                raise LogParsingError("CSV file has no headers")
            
            for line_num, row in enumerate(reader, 2):  # Start from 2 (header is line 1)
                try:
                    # Filter out None values from incomplete rows
                    cleaned_row = {k: v for k, v in row.items() if k is not None}
                    
                    if cleaned_row:  # Only process non-empty rows
                        entry = await self._create_log_entry_from_csv(cleaned_row, line_num)
                        entries.append(entry)
                        successful_parses += 1
                    else:
                        # Empty row - create placeholder entry
                        entry = await self._create_fallback_entry("", line_num, 
                                                                reason="Empty CSV row")
                        entries.append(entry)
                        
                except Exception as e:
                    # Handle malformed CSV row
                    raw_line = lines[line_num - 1] if line_num - 1 < len(lines) else ""
                    entry = await self._create_fallback_entry(raw_line, line_num, 
                                                            reason=f"CSV parse error: {str(e)}")
                    entries.append(entry)
                    
        except Exception as e:
            # Complete CSV parsing failure - fallback to plain text
            print(f"CSV parsing failed, falling back to plain text: {str(e)}")
            return await self._parse_plain_text_logs(content)
        
        # Log parsing statistics
        total_rows = len([line for line in lines[1:] if line.strip()])  # Exclude header
        if total_rows > 0:
            success_rate = successful_parses / total_rows
            print(f"CSV parsing success rate: {success_rate:.2%} ({successful_parses}/{total_rows})")
        
        return entries
    
    async def _parse_syslog_logs(self, content: str) -> List[LogEntry]:
        """Parse syslog format logs with comprehensive pattern matching"""
        entries = []
        lines = content.strip().split('\n')
        successful_parses = 0
        
        # Define syslog patterns with priority
        syslog_patterns = [
            # RFC 3164 format: <priority>timestamp hostname tag: message
            r'^<(?P<priority>\d+)>(?P<timestamp>\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+(?P<hostname>\S+)\s+(?P<tag>\S+?):\s*(?P<message>.*)$',
            # Standard syslog: timestamp hostname service: message
            r'^(?P<timestamp>\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+(?P<hostname>\S+)\s+(?P<service>\S+?):\s*(?P<message>.*)$',
            # ISO timestamp syslog: timestamp hostname service message
            r'^(?P<timestamp>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?)\s+(?P<hostname>\S+)\s+(?P<service>\S+)\s+(?P<message>.*)$',
            # Rsyslog format with structured data
            r'^(?P<timestamp>\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+(?P<hostname>\S+)\s+(?P<tag>[^:]+):\s*(?P<message>.*)$',
            # Simplified syslog: timestamp message
            r'^(?P<timestamp>\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+(?P<message>.*)$',
        ]
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
            
            parsed = False
            for pattern in syslog_patterns:
                match = re.match(pattern, line)
                if match:
                    try:
                        entry = await self._create_log_entry_from_syslog_match(match, line, line_num)
                        entries.append(entry)
                        successful_parses += 1
                        parsed = True
                        break
                    except Exception as e:
                        # Pattern matched but parsing failed
                        entry = await self._create_fallback_entry(line, line_num, 
                                                                reason=f"Syslog parse error: {str(e)}")
                        entries.append(entry)
                        parsed = True
                        break
            
            if not parsed:
                # No syslog pattern matched - treat as plain text
                entry = await self._create_log_entry_from_text(line, line_num)
                entries.append(entry)
        
        # Log parsing statistics
        total_lines = len([line for line in lines if line.strip()])
        if total_lines > 0:
            success_rate = successful_parses / total_lines
            print(f"Syslog parsing success rate: {success_rate:.2%} ({successful_parses}/{total_lines})")
        
        return entries
    
    async def _parse_structured_logs(self, content: str) -> List[LogEntry]:
        """Parse structured logs (key=value format)"""
        entries = []
        lines = content.strip().split('\n')
        successful_parses = 0
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
            
            try:
                entry = await self._create_log_entry_from_structured(line, line_num)
                entries.append(entry)
                successful_parses += 1
            except Exception as e:
                # Fallback to plain text parsing
                entry = await self._create_log_entry_from_text(line, line_num)
                entries.append(entry)
        
        return entries
    
    async def _parse_plain_text_logs(self, content: str) -> List[LogEntry]:
        """Parse plain text format logs"""
        entries = []
        lines = content.strip().split('\n')
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
            
            entry = await self._create_log_entry_from_text(line, line_num)
            entries.append(entry)
        
        return entries
    
    async def _create_log_entry_from_json(self, data: Dict[str, Any], raw_line: str, line_num: int) -> LogEntry:
        """Create LogEntry from JSON data"""
        
        # Try to extract common fields
        timestamp = await self._extract_timestamp(data.get('timestamp') or data.get('time') or data.get('@timestamp'))
        level = await self._extract_log_level(str(data.get('level', data.get('severity', ''))))
        service = await self._extract_service(data.get('service', data.get('logger', data.get('component'))))
        message = data.get('message', data.get('msg', str(data)))
        
        return LogEntry(
            timestamp=timestamp,
            level=level,
            service=service,
            message=message,
            raw_line=raw_line,
            line_number=line_num,
            metadata=data
        )
    
    async def _create_log_entry_from_csv(self, row: Dict[str, str], line_num: int) -> LogEntry:
        """Create LogEntry from CSV row"""
        
        # Common CSV column names
        timestamp_cols = ['timestamp', 'time', 'datetime', 'date']
        level_cols = ['level', 'severity', 'loglevel']
        service_cols = ['service', 'logger', 'component', 'source']
        message_cols = ['message', 'msg', 'description', 'text']
        
        timestamp = None
        level = None
        service = None
        message = ""
        
        # Find timestamp
        for col in timestamp_cols:
            if col in row and row[col]:
                timestamp = await self._extract_timestamp(row[col])
                break
        
        # Find level
        for col in level_cols:
            if col in row and row[col]:
                level = await self._extract_log_level(row[col])
                break
        
        # Find service
        for col in service_cols:
            if col in row and row[col]:
                service = await self._extract_service(row[col])
                break
        
        # Find message
        for col in message_cols:
            if col in row and row[col]:
                message = row[col]
                break
        
        # If no message found, combine all values
        if not message:
            message = " | ".join(f"{k}: {v}" for k, v in row.items() if v)
        
        raw_line = ",".join(row.values())
        
        return LogEntry(
            timestamp=timestamp,
            level=level,
            service=service,
            message=message,
            raw_line=raw_line,
            line_number=line_num,
            metadata=dict(row)
        )
    
    async def _create_log_entry_from_syslog_match(self, match: re.Match, line: str, line_num: int) -> LogEntry:
        """Create LogEntry from syslog regex match"""
        
        groups = match.groupdict()
        
        # Extract fields from match groups
        timestamp_str = groups.get('timestamp')
        hostname = groups.get('hostname')
        service = groups.get('service') or groups.get('tag')
        message = groups.get('message', '')
        priority = groups.get('priority')
        
        # Parse timestamp
        timestamp = await self._extract_timestamp(timestamp_str) if timestamp_str else None
        
        # Extract level from priority if available
        level = None
        if priority:
            try:
                severity = int(priority) % 8  # Lower 3 bits indicate severity
                if severity <= 3:
                    level = LogLevel.ERROR
                elif severity == 4:
                    level = LogLevel.WARN
                elif severity <= 6:
                    level = LogLevel.INFO
                else:
                    level = LogLevel.DEBUG
            except ValueError:
                pass
        
        # Fallback to extracting level from message
        if not level:
            level = await self._extract_log_level(message)
        
        # Extract service information
        service = await self._extract_service(service)
        
        return LogEntry(
            timestamp=timestamp,
            level=level,
            service=service,
            message=message,
            raw_line=line,
            line_number=line_num,
            metadata={'hostname': hostname, 'priority': priority}
        )
    
    async def _create_log_entry_from_structured(self, line: str, line_num: int) -> LogEntry:
        """Create LogEntry from structured log line (key=value format)"""
        
        # Parse key=value pairs
        structured_data = {}
        
        # Pattern to match key=value pairs, handling quoted values
        kv_pattern = r'(\w+)=(?:"([^"]*)"|\'([^\']*)\'|([^\s]+))'
        matches = re.findall(kv_pattern, line)
        
        for match in matches:
            key = match[0]
            value = match[1] or match[2] or match[3]  # Handle quoted and unquoted values
            structured_data[key] = value
        
        if not structured_data:
            # No key=value pairs found, treat as plain text
            return await self._create_log_entry_from_text(line, line_num)
        
        # Extract common fields
        timestamp = await self._extract_timestamp(
            structured_data.get('timestamp') or 
            structured_data.get('time') or 
            structured_data.get('ts')
        )
        level = await self._extract_log_level(
            structured_data.get('level') or 
            structured_data.get('severity') or 
            structured_data.get('loglevel', '')
        )
        service = await self._extract_service(
            structured_data.get('service') or 
            structured_data.get('component') or 
            structured_data.get('logger')
        )
        message = (
            structured_data.get('message') or 
            structured_data.get('msg') or 
            ' '.join(f"{k}={v}" for k, v in structured_data.items())
        )
        
        return LogEntry(
            timestamp=timestamp,
            level=level,
            service=service,
            message=message,
            raw_line=line,
            line_number=line_num,
            metadata=structured_data
        )
    
    async def _create_log_entry_from_text(self, line: str, line_num: int) -> LogEntry:
        """Create LogEntry from plain text line"""
        
        # Try to extract timestamp from the beginning of the line
        timestamp = None
        for pattern in self.timestamp_patterns:
            match = re.search(pattern, line)
            if match:
                timestamp = await self._extract_timestamp(match.group())
                break
        
        # Extract log level
        level = await self._extract_log_level(line)
        
        # Try to extract service/component
        service = await self._extract_service(line)
        
        return LogEntry(
            timestamp=timestamp,
            level=level,
            service=service,
            message=line,
            raw_line=line,
            line_number=line_num,
            metadata={}
        )
    
    async def _create_fallback_entry(self, line: str, line_num: int, reason: str = "Parse error") -> LogEntry:
        """Create a fallback LogEntry when parsing fails"""
        
        return LogEntry(
            timestamp=None,
            level=LogLevel.INFO,  # Default to INFO for unparseable lines
            service=None,
            message=line or "(empty line)",
            raw_line=line,
            line_number=line_num,
            metadata={"parse_error": reason}
        )
    
    async def _extract_timestamp(self, timestamp_str: Optional[str]) -> Optional[datetime]:
        """Extract datetime from timestamp string with robust format support"""
        if not timestamp_str:
            return None
        
        timestamp_str = str(timestamp_str).strip()
        
        # Enhanced timestamp formats with priority order
        formats = [
            # ISO 8601 formats
            '%Y-%m-%dT%H:%M:%S.%fZ',
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y-%m-%dT%H:%M:%S.%f',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%S%z',
            
            # Standard log formats
            '%Y-%m-%d %H:%M:%S.%f',
            '%Y-%m-%d %H:%M:%S',
            
            # Syslog formats
            '%b %d %H:%M:%S',
            '%Y %b %d %H:%M:%S',
            
            # Common variations
            '%m/%d/%Y %H:%M:%S',
            '%d/%m/%Y %H:%M:%S',
            '%Y/%m/%d %H:%M:%S',
            
            # Unix timestamp
            '%s',  # Seconds since epoch
        ]
        
        # Try parsing with each format
        for fmt in formats:
            try:
                if fmt == '%s':
                    # Handle Unix timestamp
                    timestamp = float(timestamp_str)
                    return datetime.fromtimestamp(timestamp)
                else:
                    return datetime.strptime(timestamp_str, fmt)
            except (ValueError, TypeError, OverflowError):
                continue
        
        # Try parsing relative timestamps
        if timestamp_str.isdigit():
            try:
                timestamp = int(timestamp_str)
                # Handle milliseconds or microseconds timestamps
                if timestamp > 1e10:  # Milliseconds
                    return datetime.fromtimestamp(timestamp / 1000)
                elif timestamp > 1e13:  # Microseconds
                    return datetime.fromtimestamp(timestamp / 1e6)
                else:  # Seconds
                    return datetime.fromtimestamp(timestamp)
            except (ValueError, OverflowError):
                pass
        
        # If all parsing fails, return None
        return None
    
    async def _extract_log_level(self, text: str) -> Optional[LogLevel]:
        """Extract log level from text with enhanced pattern matching"""
        if not text:
            return None
        
        text_upper = str(text).upper()
        
        # Enhanced log level patterns with priority
        enhanced_patterns = {
            LogLevel.FATAL: [r'\bFATAL\b', r'\bCRITICAL\b', r'\bEMERGENCY\b'],
            LogLevel.ERROR: [r'\bERROR\b', r'\bERR\b', r'\bFAILED\b', r'\bFAILURE\b'],
            LogLevel.WARN: [r'\bWARN\b', r'\bWARNING\b', r'\bALERT\b'],
            LogLevel.INFO: [r'\bINFO\b', r'\bINFORMATION\b', r'\bNOTICE\b'],
            LogLevel.DEBUG: [r'\bDEBUG\b', r'\bTRACE\b', r'\bVERBOSE\b'],
        }
        
        # Try enhanced patterns first
        for level, patterns in enhanced_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_upper):
                    return level
        
        # Fallback to original patterns (now lists)
        for level, patterns in self.log_level_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_upper):
                    return level
        
        return None
    
    async def _extract_service(self, service_input: Optional[str]) -> Optional[str]:
        """Extract and normalize service/component name"""
        if not service_input:
            return None
        
        service = str(service_input).strip()
        
        # If already extracted, just clean it up
        if not any(char in service for char in ['[', ']', ':', '-', ' ']):
            # Already clean service name
            return service if service.lower() not in self._get_excluded_service_names() else None
        
        # Common patterns for service names in log lines (order matters!)
        patterns = [
            r'(\w+)\[\d+\]:\s',       # service_name[pid]: message (check first)
            r'\[([^\]]+)\]',          # [service_name]
            r'(\w+):\s',              # service_name: message
            r'\b(\w+)\s*-\s',         # service_name - message
            r'(\w+)\.\w+',            # package.class
            r'(\w+):$',               # service_name: (at end)
            r'^(\w+)\s',              # service_name at start
        ]
        
        for pattern in patterns:
            match = re.search(pattern, service)
            if match:
                extracted = match.group(1)
                if extracted.lower() not in self._get_excluded_service_names():
                    return extracted
        
        # If no pattern matches, return the cleaned service name
        cleaned = re.sub(r'[^\w.-]', '', service)
        return cleaned if cleaned and cleaned.lower() not in self._get_excluded_service_names() else None
    
    def _get_excluded_service_names(self) -> set:
        """Get set of common terms that shouldn't be considered service names"""
        return {
            'info', 'error', 'warn', 'warning', 'debug', 'trace', 'fatal', 'critical',
            'log', 'logs', 'message', 'msg', 'text', 'data', 'main', 'root', 'system'
        }
import json
import time
import os
import pickle
from typing import List, Dict, Any, Optional
import httpx
from app.models.schemas import ChatMessage, ChatResponse
from app.core.config import settings


class ChatService:
    """Enhanced service for handling chat interactions with Ollama for log analysis"""
    
    def __init__(self):
        self.chat_histories: Dict[str, List[ChatMessage]] = {}
        self.file_contexts: Dict[str, Dict[str, Any]] = {}  # Store file context per session
        self.connection_healthy = True
        self.last_health_check = None
        self.health_check_interval = 300  # 5 minutes
        self.session_storage_dir = os.path.join(settings.UPLOAD_DIR, "sessions")
        self._ensure_session_dir()
    
    def _ensure_session_dir(self):
        """Ensure session storage directory exists"""
        os.makedirs(self.session_storage_dir, exist_ok=True)
    
    def _get_session_file_path(self, session_id: str) -> str:
        """Get file path for session data"""
        return os.path.join(self.session_storage_dir, f"{session_id}.pkl")
    
    def _save_session_data(self, session_id: str):
        """Save session data to disk"""
        try:
            session_data = {
                "chat_history": self.chat_histories.get(session_id, []),
                "file_context": self.file_contexts.get(session_id, {}),
                "timestamp": time.time()
            }
            
            session_file = self._get_session_file_path(session_id)
            with open(session_file, 'wb') as f:
                pickle.dump(session_data, f)
        except Exception as e:
            print(f"Warning: Failed to save session {session_id}: {e}")
    
    def _load_session_data(self, session_id: str) -> bool:
        """Load session data from disk, return True if loaded successfully"""
        try:
            session_file = self._get_session_file_path(session_id)
            if not os.path.exists(session_file):
                return False
            
            with open(session_file, 'rb') as f:
                session_data = pickle.load(f)
            
            # Restore data to memory
            if "chat_history" in session_data:
                self.chat_histories[session_id] = session_data["chat_history"]
            if "file_context" in session_data:
                self.file_contexts[session_id] = session_data["file_context"]
            
            return True
        except Exception as e:
            print(f"Warning: Failed to load session {session_id}: {e}")
            return False
    
    async def check_ollama_health(self) -> bool:
        """Check if Ollama is running and accessible"""
        
        current_time = time.time()
        
        # Skip if we checked recently and connection was healthy
        if (self.last_health_check and 
            self.connection_healthy and 
            current_time - self.last_health_check < self.health_check_interval):
            return True
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{settings.OLLAMA_URL}/api/tags")
                response.raise_for_status()
                
                # Check if our specific model is available
                models_data = response.json()
                available_models = [model["name"] for model in models_data.get("models", [])]
                model_available = settings.OLLAMA_MODEL in available_models
                
                self.connection_healthy = model_available
                self.last_health_check = current_time
                
                if not model_available:
                    print(f"Warning: {settings.OLLAMA_MODEL} not found. Available models: {available_models}")
                
                return model_available
                
        except Exception as e:
            print(f"Ollama health check failed: {str(e)}")
            self.connection_healthy = False
            self.last_health_check = current_time
            return False
    
    async def generate_response(
        self, 
        message: str, 
        file_context: Optional[Dict[str, Any]] = None,
        chat_history: List[ChatMessage] = None
    ) -> ChatResponse:
        """Generate AI response using Ollama with enhanced error handling"""
        
        # Check Ollama health first
        is_healthy = await self.check_ollama_health()
        
        if not is_healthy:
            return ChatResponse(
                response="🚫 **Ollama AI Service Unavailable**\n\n"
                       f"The AI model ({settings.OLLAMA_MODEL}) is not available. Please:\n"
                       f"1. Ensure Ollama is running: `ollama serve`\n"
                       f"2. Download the model: `ollama pull {settings.OLLAMA_MODEL}`\n"
                       f"3. Check connection to {settings.OLLAMA_URL}\n\n"
                       f"You can still view and filter log data without AI analysis.",
                context=chat_history or [],
                suggested_questions=[]
            )
        
        # Prepare optimized context prompt for log analysis
        context_prompt = self._build_log_analysis_prompt(file_context, chat_history)
        
        # Create full prompt optimized for CodeLlama
        full_prompt = self._create_codellama_prompt(context_prompt, message)
        
        try:
            # Call Ollama API with optimized parameters for CodeLlama
            async with httpx.AsyncClient(timeout=settings.OLLAMA_TIMEOUT) as client:
                response = await client.post(
                    f"{settings.OLLAMA_URL}/api/generate",
                    json={
                        "model": settings.OLLAMA_MODEL,
                        "prompt": full_prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.2,  # Lower for more focused analysis
                            "top_p": 0.8,
                            "top_k": 20,
                            "repeat_penalty": 1.1,
                            "num_predict": 1500,  # Allow longer responses for detailed analysis
                            "stop": ["Human:", "User:"]  # Stop tokens
                        }
                    }
                )
                response.raise_for_status()
                result = response.json()
                ai_response = result.get("response", "").strip()
                
                if not ai_response:
                    ai_response = "I'm sorry, I couldn't generate a response. Please try rephrasing your question."
        
        except httpx.TimeoutException:
            ai_response = ("⏰ **Request Timeout**\n\n"
                          f"The AI model took too long to respond (>{settings.OLLAMA_TIMEOUT}s). "
                          f"This might happen with complex log analysis. Please try:\n"
                          f"- Asking a more specific question\n"
                          f"- Checking if Ollama is running smoothly")
        
        except httpx.HTTPError as e:
            ai_response = (f"🌐 **Connection Error**\n\n"
                          f"Failed to connect to Ollama service: {str(e)}\n"
                          f"Please ensure Ollama is running at {settings.OLLAMA_URL}")
        
        except Exception as e:
            ai_response = (f"⚠️ **Unexpected Error**\n\n"
                          f"An error occurred while processing your request: {str(e)}\n"
                          f"Please try again or contact support if the issue persists.")
        
        # Update chat history
        updated_history = (chat_history or []).copy()
        updated_history.append(ChatMessage(role="user", content=message))
        updated_history.append(ChatMessage(role="assistant", content=ai_response))
        
        # Keep only recent history
        if len(updated_history) > settings.MAX_CHAT_HISTORY:
            updated_history = updated_history[-settings.MAX_CHAT_HISTORY:]
        
        # Generate suggested questions
        suggestions = await self._generate_suggestions_from_response(ai_response, file_context)
        
        return ChatResponse(
            response=ai_response,
            context=updated_history,
            suggested_questions=suggestions
        )
    
    async def get_chat_history(self, session_id: str) -> List[ChatMessage]:
        """Get chat history for a session"""
        # Try to load from disk if not in memory
        if session_id not in self.chat_histories:
            self._load_session_data(session_id)
        
        return self.chat_histories.get(session_id, [])
    
    async def clear_chat_history(self, session_id: str):
        """Clear chat history for a session"""
        if session_id in self.chat_histories:
            del self.chat_histories[session_id]
    
    async def generate_suggestions(self, file_context: Dict[str, Any]) -> List[str]:
        """Generate suggested questions based on file context"""
        
        suggestions = []
        
        # Basic suggestions based on file content
        if file_context:
            total_entries = file_context.get("total_entries", 0)
            error_entries = file_context.get("error_entries", [])
            services = file_context.get("services", {})
            level_distribution = file_context.get("level_distribution", {})
            
            if total_entries > 0:
                suggestions.append(f"What are the main patterns in these {total_entries:,} log entries?")
            
            if error_entries:
                suggestions.append("Show me the most common error types")
                suggestions.append("What caused the recent errors?")
            
            if services:
                top_service = max(services.keys(), key=lambda k: services[k]) if services else None
                if top_service:
                    suggestions.append(f"Tell me about errors from {top_service}")
            
            if "ERROR" in level_distribution or "WARN" in level_distribution:
                suggestions.append("Are there any error patterns I should be concerned about?")
            
            suggestions.extend([
                "Summarize the log activity over time",
                "What anomalies do you detect in the logs?",
                "Which services are generating the most logs?",
                "Are there any performance issues indicated?"
            ])
        
        # Default suggestions if no context
        if not suggestions:
            suggestions = [
                "What patterns do you see in these logs?",
                "Are there any errors I should investigate?",
                "Summarize the log activity",
                "What services are most active?"
            ]
        
        return suggestions[:5]  # Return top 5 suggestions
    
    def _build_context_prompt(
        self, 
        file_context: Optional[Dict[str, Any]] = None,
        chat_history: List[ChatMessage] = None
    ) -> str:
        """Build context prompt for AI"""
        
        prompt_parts = [
            "You are an expert log analyst helping analyze system logs. Be concise and focus on actionable insights.",
            "You should identify patterns, anomalies, errors, and provide clear explanations."
        ]
        
        if file_context:
            prompt_parts.append("\n--- LOG FILE CONTEXT ---")
            
            # Basic stats
            total_entries = file_context.get("total_entries", 0)
            if total_entries > 0:
                prompt_parts.append(f"Total log entries: {total_entries:,}")
            
            # Date range
            date_range = file_context.get("date_range", {})
            if date_range.get("start") and date_range.get("end"):
                prompt_parts.append(f"Time range: {date_range['start']} to {date_range['end']}")
            
            # Level distribution
            level_distribution = file_context.get("level_distribution", {})
            if level_distribution:
                level_summary = []
                for level, count in level_distribution.items():
                    if hasattr(level, 'value'):
                        level_name = level.value
                    else:
                        level_name = str(level)
                    level_summary.append(f"{level_name}: {count}")
                prompt_parts.append(f"Log levels: {', '.join(level_summary)}")
            
            # Services
            services = file_context.get("services", {})
            if services:
                top_services = list(services.items())[:5]  # Top 5 services
                service_summary = [f"{name}: {count}" for name, count in top_services]
                prompt_parts.append(f"Top services: {', '.join(service_summary)}")
            
            # Sample entries
            sample_entries = file_context.get("sample_entries", [])
            if sample_entries:
                prompt_parts.append("\n--- SAMPLE LOG ENTRIES ---")
                for i, entry in enumerate(sample_entries[:5]):
                    timestamp = entry.get("timestamp", "")
                    level = entry.get("level", "")
                    message = entry.get("message", "")[:100]  # Truncate long messages
                    prompt_parts.append(f"{i+1}. [{timestamp}] {level}: {message}")
            
            # Error examples
            error_entries = file_context.get("error_entries", [])
            if error_entries:
                prompt_parts.append("\n--- ERROR EXAMPLES ---")
                for i, entry in enumerate(error_entries[:3]):
                    timestamp = entry.get("timestamp", "")
                    message = entry.get("message", "")[:150]
                    prompt_parts.append(f"{i+1}. [{timestamp}] {message}")
        
        # Chat history context
        if chat_history:
            prompt_parts.append("\n--- PREVIOUS CONVERSATION ---")
            for msg in chat_history[-6:]:  # Last 3 exchanges
                role_prefix = "Human" if msg.role == "user" else "Assistant"
                content = msg.content[:200]  # Truncate long messages
                prompt_parts.append(f"{role_prefix}: {content}")
        
        prompt_parts.append("\nPlease provide a helpful, accurate response based on the log data above.")
        
        return "\n".join(prompt_parts)
    
    def _build_log_analysis_prompt(
        self, 
        file_context: Optional[Dict[str, Any]] = None,
        chat_history: List[ChatMessage] = None
    ) -> str:
        """Build specialized context prompt for log analysis with CodeLlama"""
        
        prompt_parts = [
            "You are an expert log analyst and system engineer. Analyze system logs to provide actionable insights.",
            "Focus on: error patterns, performance issues, security concerns, anomalies, and operational insights.",
            "Be specific, technical, and provide concrete recommendations when possible."
        ]
        
        if file_context:
            prompt_parts.append("\n=== LOG FILE ANALYSIS ===")
            
            # File summary
            total_entries = file_context.get("total_entries", 0)
            if total_entries > 0:
                prompt_parts.append(f"📊 Total Entries: {total_entries:,}")
            
            # Time range analysis
            date_range = file_context.get("date_range", {})
            if date_range.get("start") and date_range.get("end"):
                prompt_parts.append(f"⏰ Time Range: {date_range['start']} → {date_range['end']}")
            
            # Critical statistics
            level_distribution = file_context.get("level_distribution", {})
            if level_distribution:
                error_count = level_distribution.get("ERROR", 0)
                warn_count = level_distribution.get("WARN", 0) + level_distribution.get("WARNING", 0)
                info_count = level_distribution.get("INFO", 0)
                debug_count = level_distribution.get("DEBUG", 0)
                
                if error_count > 0:
                    prompt_parts.append(f" ERRORS: {error_count}")
                if warn_count > 0:
                    prompt_parts.append(f" WARNINGS: {warn_count}")
                if info_count > 0:
                    prompt_parts.append(f" INFO: {info_count}")
                if debug_count > 0:
                    prompt_parts.append(f" DEBUG: {debug_count}")
            
            # Service analysis
            services = file_context.get("services", {})
            if services:
                top_services = list(services.items())[:8]  # Top services
                prompt_parts.append(f"🏗️  Services: {dict(top_services)}")
            
            # Error patterns with more detail
            error_entries = file_context.get("error_entries", [])
            if error_entries:
                prompt_parts.append(f"\n=== ACTUAL ERROR ENTRIES ({len(error_entries)} found) ===")
                for i, entry in enumerate(error_entries[:5]):  # Top 5 errors
                    timestamp = entry.get("timestamp", "unknown")
                    service = entry.get("service", "unknown")
                    message = entry.get("message", "")[:300]  # More context
                    prompt_parts.append(f"ERROR {i+1}: Time=[{timestamp}] Service=[{service}]")
                    prompt_parts.append(f"   Message: {message}")
            
            # Warning patterns
            warning_entries = file_context.get("warning_entries", [])
            if warning_entries:
                prompt_parts.append(f"\n=== ACTUAL WARNING ENTRIES ({len(warning_entries)} found) ===")
                for i, entry in enumerate(warning_entries[:3]):
                    timestamp = entry.get("timestamp", "unknown")
                    service = entry.get("service", "unknown") 
                    message = entry.get("message", "")[:200]
                    prompt_parts.append(f"WARN {i+1}: [{timestamp}] {service}: {message}")
            
            # Sample entries for pattern recognition (always show some)
            sample_entries = file_context.get("sample_entries", [])
            if sample_entries:
                prompt_parts.append(f"\n=== SAMPLE LOG ENTRIES ===")
                for i, entry in enumerate(sample_entries[:5]):  # Show more samples
                    timestamp = entry.get("timestamp", "")
                    level = entry.get("level", "")
                    service = entry.get("service", "unknown")
                    message = entry.get("message", "")[:150]
                    prompt_parts.append(f"SAMPLE {i+1}: [{timestamp}] {level} [{service}] {message}")
            
            # Add specific patterns if available
            patterns = file_context.get("error_patterns", [])
            if patterns:
                prompt_parts.append(f"\n=== DETECTED ERROR PATTERNS ===")
                for i, pattern in enumerate(patterns[:3]):
                    prompt_parts.append(f"PATTERN {i+1}: {pattern}")
        
        # Conversation context
        if chat_history:
            prompt_parts.append(f"\n=== CONVERSATION HISTORY ===")
            for msg in chat_history[-4:]:  # Last 2 exchanges
                role_prefix = "👤 User" if msg.role == "user" else "🤖 Assistant"
                content = msg.content[:250]
                prompt_parts.append(f"{role_prefix}: {content}")
        
        prompt_parts.append("\nProvide detailed, technical analysis with specific recommendations.")
        
        return "\n".join(prompt_parts)
    
    def _create_codellama_prompt(self, context: str, user_message: str) -> str:
        """Create CodeLlama-optimized prompt for log analysis"""
        
        return f"""<|system|>
{context}

You are a log analysis expert. Answer questions based ONLY on the provided log data above. 

CRITICAL RULES:
1. If the information is NOT in the provided logs, respond EXACTLY with: "I can't find that information in the provided logs"
2. Be specific - reference actual log entries, timestamps, services, and error messages from the data
3. Avoid generic advice - focus on what the actual logs show
4. When mentioning numbers, use the exact counts from the log data
5. Reference specific services, timestamps, and error patterns from the provided context
6. Never make assumptions or provide information not explicitly shown in the log data

Provide actionable insights based on the actual log entries shown above.
<|/system|>

<|user|>
{user_message}
<|/user|>

<|assistant|>
Based on the provided log data, """
    
    async def _generate_suggestions_from_response(
        self, 
        ai_response: str, 
        file_context: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """Generate follow-up suggestions based on AI response"""
        
        suggestions = []
        
        # Analyze the response to suggest follow-ups
        response_lower = ai_response.lower()
        
        if "error" in response_lower:
            suggestions.extend([
                "What's the root cause of these errors?",
                "How can I prevent these errors?",
                "Show me the timeline of errors"
            ])
        
        if "pattern" in response_lower or "frequent" in response_lower:
            suggestions.extend([
                "Are these patterns normal or concerning?",
                "What services are affected by these patterns?"
            ])
        
        if "anomaly" in response_lower or "unusual" in response_lower:
            suggestions.extend([
                "What caused these anomalies?",
                "Should I be concerned about these anomalies?"
            ])
        
        if "performance" in response_lower:
            suggestions.extend([
                "What's causing the performance issues?",
                "How severe are these performance problems?"
            ])
        
        # Add some generic follow-ups
        suggestions.extend([
            "Can you explain this in more detail?",
            "What should I investigate next?",
            "Are there any other concerning patterns?"
        ])
        
        # Remove duplicates and limit
        unique_suggestions = list(dict.fromkeys(suggestions))
        return unique_suggestions[:4]
    
    async def test_ollama_integration(self, sample_log_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Test Ollama integration with sample log data"""
        
        test_results = {
            "health_check": False,
            "model_available": False,
            "response_generation": False,
            "response_time": None,
            "error_message": None,
            "sample_response": None
        }
        
        try:
            # 1. Health check
            start_time = time.time()
            health_status = await self.check_ollama_health()
            test_results["health_check"] = health_status
            
            if not health_status:
                test_results["error_message"] = "Ollama health check failed"
                return test_results
            
            test_results["model_available"] = True
            
            # 2. Test response generation with sample data
            if not sample_log_data:
                sample_log_data = {
                    "total_entries": 1500,
                    "date_range": {"start": "2024-08-24T10:00:00Z", "end": "2024-08-24T18:00:00Z"},
                    "level_distribution": {"ERROR": 45, "WARN": 123, "INFO": 1200, "DEBUG": 132},
                    "services": {"web-server": 800, "database": 400, "cache": 200, "auth": 100},
                    "error_entries": [
                        {
                            "timestamp": "2024-08-24T15:30:00Z",
                            "service": "database",
                            "message": "Connection pool exhausted - max connections: 100"
                        },
                        {
                            "timestamp": "2024-08-24T16:45:00Z", 
                            "service": "web-server",
                            "message": "HTTP 500 - Internal server error in user authentication"
                        }
                    ],
                    "sample_entries": [
                        {
                            "timestamp": "2024-08-24T14:20:00Z",
                            "level": "INFO",
                            "service": "web-server", 
                            "message": "Request processed successfully: GET /api/users"
                        }
                    ]
                }
            
            # Test with a typical log analysis question
            test_message = "What are the main issues in these logs and what should I investigate first?"
            
            response = await self.generate_response(
                message=test_message,
                file_context=sample_log_data,
                chat_history=[]
            )
            
            end_time = time.time()
            test_results["response_time"] = round(end_time - start_time, 2)
            test_results["response_generation"] = True
            test_results["sample_response"] = response.response[:500]  # First 500 chars
            
        except Exception as e:
            test_results["error_message"] = str(e)
        
        return test_results
    
    async def set_file_context(self, session_id: str, file_context: Dict[str, Any]):
        """Store file context for a session to maintain persistence across views"""
        # Try to load existing session first
        self._load_session_data(session_id)
        
        # Update context
        self.file_contexts[session_id] = file_context
        
        # Save to disk
        self._save_session_data(session_id)
    
    async def get_file_context(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve stored file context for a session"""
        # Try to load from disk if not in memory
        if session_id not in self.file_contexts:
            self._load_session_data(session_id)
        
        return self.file_contexts.get(session_id)
    
    async def generate_session_response(
        self,
        session_id: str,
        message: str,
        file_context: Optional[Dict[str, Any]] = None
    ) -> ChatResponse:
        """Generate response with session-based context persistence"""
        
        # Use provided context or retrieve from session
        if file_context:
            await self.set_file_context(session_id, file_context)
        else:
            file_context = await self.get_file_context(session_id)
        
        # Get chat history for this session
        chat_history = await self.get_chat_history(session_id)
        
        # Generate response
        response = await self.generate_response(
            message=message,
            file_context=file_context,
            chat_history=chat_history
        )
        
        # Update session chat history
        self.chat_histories[session_id] = response.context
        
        # Save session data persistently
        self._save_session_data(session_id)
        
        return response
    
    async def clear_session(self, session_id: str):
        """Clear all data for a session"""
        # Clear from memory
        if session_id in self.chat_histories:
            del self.chat_histories[session_id]
        if session_id in self.file_contexts:
            del self.file_contexts[session_id]
        
        # Remove from disk
        try:
            session_file = self._get_session_file_path(session_id)
            if os.path.exists(session_file):
                os.remove(session_file)
        except Exception as e:
            print(f"Warning: Failed to remove session file {session_id}: {e}")
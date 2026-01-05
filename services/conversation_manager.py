"""Conversation session manager for WhatsApp chat history."""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from loguru import logger


class ConversationManager:
    """Manages conversation sessions and history in memory."""

    def __init__(self, max_history: int = 10, timeout_minutes: int = 30):
        """
        Initialize conversation manager.

        Args:
            max_history: Maximum number of messages to keep per session
            timeout_minutes: Session timeout in minutes
        """
        self.sessions: Dict[str, Dict] = {}
        self.max_history = max_history
        self.timeout_minutes = timeout_minutes
        logger.info(
            f"ConversationManager initialized with max_history={max_history}, "
            f"timeout={timeout_minutes}min"
        )

    def _is_session_expired(self, session: Dict) -> bool:
        """Check if a session has expired."""
        last_activity = session.get("last_activity")
        if not last_activity:
            return True
        timeout = timedelta(minutes=self.timeout_minutes)
        return datetime.now() - last_activity > timeout

    def _clean_expired_sessions(self):
        """Remove expired sessions from memory."""
        expired_keys = [
            phone for phone, session in self.sessions.items()
            if self._is_session_expired(session)
        ]
        for key in expired_keys:
            logger.info(f"Cleaning expired session: {key}")
            del self.sessions[key]

    def get_conversation_history(self, phone_number: str) -> List[Dict[str, str]]:
        """
        Get conversation history for a phone number.

        Args:
            phone_number: User's phone number

        Returns:
            List of message dictionaries with 'role' and 'content'
        """
        self._clean_expired_sessions()

        if phone_number not in self.sessions:
            logger.info(f"New conversation session started: {phone_number}")
            self.sessions[phone_number] = {
                "messages": [],
                "last_activity": datetime.now(),
            }
            return []

        session = self.sessions[phone_number]

        # Check if session expired
        if self._is_session_expired(session):
            logger.info(f"Session expired, starting fresh: {phone_number}")
            self.sessions[phone_number] = {
                "messages": [],
                "last_activity": datetime.now(),
            }
            return []

        # Update last activity
        session["last_activity"] = datetime.now()
        return session["messages"]

    def add_message(self, phone_number: str, role: str, content: str):
        """
        Add a message to conversation history.

        Args:
            phone_number: User's phone number
            role: Message role ('user' or 'assistant')
            content: Message content
        """
        if phone_number not in self.sessions:
            self.sessions[phone_number] = {
                "messages": [],
                "last_activity": datetime.now(),
            }

        session = self.sessions[phone_number]
        session["messages"].append({"role": role, "content": content})
        session["last_activity"] = datetime.now()

        # Keep only recent messages
        if len(session["messages"]) > self.max_history:
            session["messages"] = session["messages"][-self.max_history :]

        logger.debug(
            f"Added {role} message to {phone_number}. "
            f"History length: {len(session['messages'])}"
        )

    def clear_session(self, phone_number: str):
        """
        Clear conversation history for a phone number.

        Args:
            phone_number: User's phone number
        """
        if phone_number in self.sessions:
            del self.sessions[phone_number]
            logger.info(f"Cleared session: {phone_number}")

    def get_active_sessions_count(self) -> int:
        """Get count of active sessions."""
        self._clean_expired_sessions()
        return len(self.sessions)

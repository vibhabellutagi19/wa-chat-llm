"""Database-backed conversation manager for WhatsApp chat history."""
from typing import Dict, List, Optional
from loguru import logger

from services.database import DatabaseService


class ConversationManagerDB:
    """Manages conversation sessions and history using PostgreSQL."""

    def __init__(self, max_history: int = 10):
        """
        Initialize conversation manager with database backend.

        Args:
            max_history: Maximum number of messages to return per query
        """
        self.db = DatabaseService()
        self.max_history = max_history
        logger.info(
            f"ConversationManagerDB initialized with max_history={max_history}"
        )

    def get_conversation_history(
        self, phone_number: str, full_name: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """
        Get conversation history for a phone number from database.

        Args:
            phone_number: User's phone number
            full_name: User's display name (optional, for update)

        Returns:
            List of message dictionaries with 'role' and 'content'
        """
        # Update user name if provided
        if full_name:
            self.db.get_or_create_user(phone_number, full_name=full_name)

        messages = self.db.get_conversation_history(
            phone_number, limit=self.max_history
        )

        logger.debug(
            f"Retrieved {len(messages)} messages for {phone_number}"
        )
        return messages

    def add_message(
        self, phone_number: str, role: str, content: str, full_name: Optional[str] = None
    ):
        """
        Add a message to conversation history in database.

        Args:
            phone_number: User's phone number
            role: Message role ('user' or 'assistant')
            content: Message content
            full_name: User's display name (optional)
        """
        self.db.add_message(phone_number, role, content, full_name=full_name)
        logger.debug(
            f"Added {role} message to {phone_number} in database"
        )

    def clear_session(self, phone_number: str):
        """
        Clear conversation history for a phone number (mark chat as inactive).

        Args:
            phone_number: User's phone number
        """
        self.db.clear_conversation(phone_number)
        logger.info(f"Cleared session for {phone_number} in database")

    def get_active_sessions_count(self) -> int:
        """
        Get count of active chat sessions.

        Returns:
            Number of active chats
        """
        # This would require a new DB query - implement if needed
        return 0  # Placeholder

    def get_user_stats(self, phone_number: str) -> Dict:
        """
        Get statistics for a user.

        Args:
            phone_number: User's phone number

        Returns:
            Dictionary with user stats
        """
        return self.db.get_user_stats(phone_number)

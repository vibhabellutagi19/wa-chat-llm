"""Database service for PostgreSQL operations."""
import json
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Optional
from contextlib import contextmanager

import psycopg2
from psycopg2.extras import RealDictCursor, Json
from loguru import logger

from config.settings import settings
from services.whatsapp_utils import clean_phone_number


class DatabaseService:
    """Service for managing PostgreSQL database operations."""

    def __init__(self):
        """Initialize database connection."""
        self.connection_params = {
            "host": settings.POSTGRES_HOST,
            "port": settings.POSTGRES_PORT,
            "database": settings.POSTGRES_DB,
            "user": settings.POSTGRES_USER,
            "password": settings.POSTGRES_PASSWORD,
        }
        logger.info("DatabaseService initialized")

    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = None
        try:
            conn = psycopg2.connect(**self.connection_params)
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def get_or_create_user(
        self, phone_number: str, full_name: Optional[str] = None, email: Optional[str] = None
    ) -> Dict:
        """
        Get existing user or create new one.

        Args:
            phone_number: Phone number from Twilio (will be cleaned to E.164 format)
            full_name: User's full name from WhatsApp profile
            email: User's email (optional)

        Returns:
            User record as dictionary
        """
        # Clean phone number to E.164 format (+1234567890)
        clean_phone = clean_phone_number(phone_number)

        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Try to get existing user
                cur.execute(
                    "SELECT * FROM users WHERE phone_number = %s", (clean_phone,)
                )
                user = cur.fetchone()

                if user:
                    # Update name if provided and different
                    if full_name and user["full_name"] != full_name:
                        cur.execute(
                            "UPDATE users SET full_name = %s WHERE user_id = %s",
                            (full_name, user["user_id"]),
                        )
                        user["full_name"] = full_name
                    logger.debug(f"Found existing user: {user['user_id']}")
                    return dict(user)

                # Create new user
                cur.execute(
                    """
                    INSERT INTO users (phone_number, full_name, email)
                    VALUES (%s, %s, %s)
                    RETURNING *
                    """,
                    (clean_phone, full_name, email),
                )
                user = cur.fetchone()
                logger.info(f"Created new user: {user['user_id']} ({clean_phone})")
                return dict(user)

    def get_or_create_chat(self, phone_number: str) -> Dict:
        """
        Get active chat for user or create new one.

        Args:
            phone_number: Phone number from Twilio (will be cleaned)

        Returns:
            Chat record with messages
        """
        # Phone number will be cleaned in get_or_create_user
        user = self.get_or_create_user(phone_number)
        user_id = user["user_id"]

        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Get active chat
                cur.execute(
                    """
                    SELECT * FROM userchats
                    WHERE customer_id = %s AND is_active = true
                    ORDER BY created_at DESC
                    LIMIT 1
                    """,
                    (user_id,),
                )
                chat = cur.fetchone()

                if chat:
                    logger.debug(f"Found active chat: {chat['chat_id']}")
                    return dict(chat)

                # Create new chat with unique ID
                chat_id = uuid.uuid4().hex[:16]  # 16 char hex string
                cur.execute(
                    """
                    INSERT INTO userchats (chat_id, customer_id)
                    VALUES (%s, %s)
                    RETURNING *
                    """,
                    (chat_id, user_id),
                )
                chat = cur.fetchone()
                logger.info(f"Created new chat: {chat_id} for user {user_id}")
                return dict(chat)

    def add_message(
        self, phone_number: str, role: str, content: str, full_name: Optional[str] = None
    ):
        """
        Add message to chat history.

        Args:
            phone_number: Phone number from Twilio (will be cleaned)
            role: Message role ('user' or 'assistant')
            content: Message content
            full_name: User's display name (optional)
        """
        # Ensure user exists with updated name
        if full_name:
            self.get_or_create_user(phone_number, full_name=full_name)

        chat = self.get_or_create_chat(phone_number)

        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE userchats
                    SET messages = messages || %s::jsonb
                    WHERE chat_id = %s
                    """,
                    (Json([message]), chat["chat_id"]),
                )
                logger.debug(
                    f"Added {role} message to chat {chat['chat_id']}"
                )

    def get_conversation_history(
        self, phone_number: str, limit: Optional[int] = None
    ) -> List[Dict[str, str]]:
        """
        Get conversation history for a user.

        Args:
            phone_number: Phone number from Twilio (will be cleaned)
            limit: Maximum number of messages to return

        Returns:
            List of message dictionaries
        """
        chat = self.get_or_create_chat(phone_number)
        messages = chat.get("messages", [])

        if not messages:
            return []

        # Return last N messages if limit specified
        if limit:
            messages = messages[-limit:]

        logger.debug(
            f"Retrieved {len(messages)} messages for {phone_number}"
        )
        return messages

    def clear_conversation(self, phone_number: str):
        """
        End current chat session and start fresh.

        Args:
            phone_number: Phone number from Twilio (will be cleaned)
        """
        user = self.get_or_create_user(phone_number)

        with self.get_connection() as conn:
            with conn.cursor() as cur:
                # Deactivate current chat
                cur.execute(
                    """
                    UPDATE userchats
                    SET is_active = false
                    WHERE customer_id = %s AND is_active = true
                    """,
                    (user["user_id"],),
                )
                logger.info(f"Cleared conversation for {phone_number}")

    def get_user_stats(self, phone_number: str) -> Dict:
        """
        Get statistics for a user.

        Args:
            phone_number: Phone number from Twilio (will be cleaned)

        Returns:
            Dictionary with user stats
        """
        user = self.get_or_create_user(phone_number)

        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT
                        COUNT(*) as total_chats,
                        SUM(jsonb_array_length(messages)) as total_messages
                    FROM userchats
                    WHERE customer_id = %s
                    """,
                    (user["user_id"],),
                )
                stats = cur.fetchone()
                return {
                    "user_id": str(user["user_id"]),
                    "phone_number": phone_number,
                    "full_name": user.get("full_name"),
                    "total_chats": stats["total_chats"] or 0,
                    "total_messages": stats["total_messages"] or 0,
                }

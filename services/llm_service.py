"""OpenAI LLM service for generating responses."""
from typing import List, Dict, Optional
from openai import OpenAI
from loguru import logger

from config.settings import settings
from config.prompts import get_system_prompt


class LLMService:
    """Service for interacting with OpenAI LLM."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize LLM service.

        Args:
            api_key: OpenAI API key (defaults to settings)
            model: Model name (defaults to settings)
        """
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model or settings.OPENAI_MODEL

        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is required")

        self.client = OpenAI(api_key=self.api_key)
        logger.info(f"LLMService initialized with model: {self.model}")

    def generate_response(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Generate a response using OpenAI.

        Args:
            user_message: Current user message
            conversation_history: Previous messages (list of {role, content} dicts)
            system_prompt: Custom system prompt (defaults to data engineering expert)
            temperature: Sampling temperature (defaults to settings)
            max_tokens: Maximum tokens in response (defaults to settings)

        Returns:
            Generated response text
        """
        # Build messages list
        messages = []

        # Add system prompt
        if system_prompt is None:
            system_prompt = get_system_prompt("data_engineering")
        messages.append({"role": "system", "content": system_prompt})

        # Add conversation history
        if conversation_history:
            messages.extend(conversation_history)

        # Add current user message
        messages.append({"role": "user", "content": user_message})

        # Set parameters
        temp = temperature if temperature is not None else settings.LLM_TEMPERATURE
        max_tok = max_tokens if max_tokens is not None else settings.LLM_MAX_TOKENS

        logger.debug(
            f"Generating response with {len(messages)} messages, "
            f"temp={temp}, max_tokens={max_tok}"
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temp,
                max_tokens=max_tok,
                n=1,
            )

            content = response.choices[0].message.content
            logger.info(f"Generated response: {len(content)} characters")
            return content

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "Sorry, I encountered an error processing your request. Please try again."

    def generate_simple_response(self, user_message: str) -> str:
        """
        Generate a simple response without conversation history.

        Args:
            user_message: User message

        Returns:
            Generated response text
        """
        return self.generate_response(user_message, conversation_history=None)

from fastapi import FastAPI, Request, Form, HTTPException, Header
from fastapi.responses import Response
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from twilio.request_validator import RequestValidator
from loguru import logger
from typing import Optional

from config.settings import settings
from services.llm_service import LLMService
from services.conversation_manager import ConversationManager
from services.conversation_manager_db import ConversationManagerDB
from services.whatsapp_utils import format_for_twilio

app = FastAPI(title="Twilio WhatsApp LLM Bot")

# Initialize services
try:
    if not settings.validate():
        raise ValueError("Missing required environment variables. Check your .env file.")

    twilio_client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    validator = RequestValidator(settings.TWILIO_AUTH_TOKEN)
    llm_service = LLMService()

    # Choose storage backend based on configuration
    if settings.STORAGE_BACKEND == "database":
        conversation_manager = ConversationManagerDB(
            max_history=settings.MAX_CONVERSATION_HISTORY
        )
        logger.info("Using PostgreSQL database backend for conversation storage")
    else:
        conversation_manager = ConversationManager(
            max_history=settings.MAX_CONVERSATION_HISTORY,
            timeout_minutes=settings.SESSION_TIMEOUT_MINUTES,
        )
        logger.info("Using in-memory backend for conversation storage")

    logger.info("All services initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize services: {e}")
    raise

# Webhook endpoint to receive messages
@app.post("/chat/whatsapp")
async def whatsapp_webhook(
    request: Request,
    From: str = Form(...),
    Body: str = Form(...),
    MessageSid: str = Form(...),
    NumMedia: int = Form(0),
    ProfileName: Optional[str] = Form(None),  # WhatsApp display name
    x_twilio_signature: Optional[str] = Header(None, alias="X-Twilio-Signature"),
):
    """
    Receives incoming WhatsApp messages from Twilio and responds with LLM-generated text.
    Validates that requests come from Twilio using request signature validation.
    """
    # Validate Twilio request signature
    url = str(request.url)
    form_data = await request.form()
    params = dict(form_data)

    if not validator.validate(url, params, x_twilio_signature or ""):
        logger.warning(f"Invalid Twilio signature for request from {request.client.host}")
        raise HTTPException(status_code=403, detail="Invalid Twilio signature")

    sender = From  # Format: whatsapp:+1234567890
    message_body = Body
    profile_name = ProfileName  # User's WhatsApp display name

    logger.info(
        f"Received message from {sender} ({profile_name}) (SID: {MessageSid}): {message_body[:50]}..."
    )

    # Process the message with LLM
    response_text = await process_message(message_body, sender, profile_name)

    # Create TwiML response
    resp = MessagingResponse()
    resp.message(response_text)

    return Response(content=str(resp), media_type="application/xml")


async def process_message(message: str, sender: str, profile_name: Optional[str] = None) -> str:
    """
    Process incoming message with LLM and conversation history.

    Args:
        message: User's message
        sender: User's phone number (whatsapp:+1234567890)
        profile_name: User's WhatsApp display name

    Returns:
        LLM-generated response
    """
    try:
        # Handle special commands
        if message.lower().strip() in ["clear", "reset", "start over"]:
            conversation_manager.clear_session(sender)
            return "Conversation cleared. Let's start fresh! How can I help you with data engineering?"

        # Get conversation history (pass profile_name if using database backend)
        if isinstance(conversation_manager, ConversationManagerDB):
            history = conversation_manager.get_conversation_history(sender, full_name=profile_name)
        else:
            history = conversation_manager.get_conversation_history(sender)

        # Print conversation history for debugging
        logger.info(f"=== Conversation History for {sender} ({profile_name}) ===")
        logger.info(f"Number of messages in history: {len(history)}")
        for idx, msg in enumerate(history, 1):
            logger.info(f"  [{idx}] {msg['role']}: {msg['content'][:100]}...")
        logger.info(f"=== End History ===")

        # Generate LLM response
        response = llm_service.generate_response(
            user_message=message, conversation_history=history
        )

        # Save messages to history (with profile_name for database)
        if isinstance(conversation_manager, ConversationManagerDB):
            conversation_manager.add_message(sender, "user", message, full_name=profile_name)
            conversation_manager.add_message(sender, "assistant", response, full_name=profile_name)
        else:
            conversation_manager.add_message(sender, "user", message)
            conversation_manager.add_message(sender, "assistant", response)

        logger.info(f"Responded to {sender}: {response[:50]}...")
        return response

    except Exception as e:
        logger.error(f"Error processing message from {sender}: {e}")
        return "Sorry, I encountered an error. Please try again or type 'clear' to reset our conversation."

# Function to send outbound messages
def send_whatsapp_message(to_number: str, message: str):
    """
    Send a WhatsApp message to a user.

    Args:
        to_number: Phone number in format whatsapp:+1234567890
        message: Message text to send

    Returns:
        Dict with status and message SID or error
    """
    try:
        msg = twilio_client.messages.create(
            from_=settings.TWILIO_WHATSAPP_NUMBER, body=message, to=to_number
        )
        logger.info(f"Sent message to {to_number}: {msg.sid}")
        return {"status": "sent", "sid": msg.sid}
    except Exception as e:
        logger.error(f"Error sending message to {to_number}: {e}")
        return {"status": "error", "message": str(e)}


# Example endpoint to trigger outbound message
@app.post("/send-message")
async def send_message(phone_number: str, message: str):
    """
    API endpoint to send WhatsApp messages.

    Args:
        phone_number: Phone number with country code (e.g., +1234567890)
        message: Message text to send

    Returns:
        Result with status
    """
    # Format for Twilio (adds whatsapp: prefix)
    whatsapp_number = format_for_twilio(phone_number)
    result = send_whatsapp_message(whatsapp_number, message)
    return result


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Twilio WhatsApp LLM Bot API",
        "version": "1.0.0",
        "endpoints": {
            "webhook": "/webhook/whatsapp",
            "send": "/send-message",
            "health": "/health",
            "stats": "/stats",
        },
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "services": {
            "twilio": bool(settings.TWILIO_ACCOUNT_SID)
        },
    }


@app.get("/stats")
async def get_stats():
    """Get conversation statistics."""
    return {
        "active_sessions": conversation_manager.get_active_sessions_count(),
        "max_history": settings.MAX_CONVERSATION_HISTORY,
        "session_timeout_minutes": settings.SESSION_TIMEOUT_MINUTES,
    }
"""Utility functions for WhatsApp integration."""
from typing import Optional
from loguru import logger


def clean_phone_number(phone: str) -> str:
    """
    Extract clean phone number from Twilio format.

    Removes 'whatsapp:' prefix and returns just the E.164 number.

    Args:
        phone: Phone number from Twilio (e.g., 'whatsapp:+1234567890' or '+1234567890')

    Returns:
        Clean phone number in E.164 format: +1234567890

    Examples:
        >>> clean_phone_number('whatsapp:+1234567890')
        '+1234567890'
        >>> clean_phone_number('+1234567890')
        '+1234567890'
    """
    if phone.startswith("whatsapp:"):
        phone = phone.replace("whatsapp:", "")

    # Ensure it starts with +
    if not phone.startswith("+"):
        phone = f"+{phone}"

    logger.debug(f"Cleaned phone number: {phone}")
    return phone


def format_for_twilio(phone: str) -> str:
    """
    Format phone number for Twilio WhatsApp API.

    Args:
        phone: Phone number (e.g., '+1234567890' or 'whatsapp:+1234567890')

    Returns:
        Phone number in Twilio WhatsApp format: whatsapp:+1234567890
    """
    phone = clean_phone_number(phone)
    return f"whatsapp:{phone}"


def extract_profile_name_from_webhook(form_data: dict) -> Optional[str]:
    """
    Extract WhatsApp profile name from Twilio webhook form data.

    Args:
        form_data: Form data from Twilio webhook request

    Returns:
        Profile name if present, None otherwise
    """
    profile_name = form_data.get("ProfileName")
    if profile_name:
        logger.debug(f"Extracted profile name: {profile_name}")
        return profile_name
    return None

#!/usr/bin/env python3
"""
WhatsApp Sender - Digital FTE System
Sends WhatsApp messages using WhatsApp Business API.

Usage:
    python whatsapp_sender.py "content"
    python whatsapp_sender.py "content" --dry-run

Environment Variables Required:
    WHATSAPP_PHONE_NUMBER_ID
    WHATSAPP_ACCESS_TOKEN
"""

import os
import sys
import logging
import argparse
import requests
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Import shared utilities
try:
    from social_media_utils import (
        parse_markdown_field,
        parse_markdown_list,
        log_social_post,
        get_env_var,
        validate_text_length
    )
except ImportError:
    print("Error: social_media_utils.py not found")
    sys.exit(1)

# Load environment variables
load_dotenv()

# Configuration
BASE_DIR = Path(__file__).parent.resolve()
LOGS_DIR = BASE_DIR / "Logs"
LOGS_DIR.mkdir(exist_ok=True)

# Logging setup
LOG_FILE = LOGS_DIR / "whatsapp_sender.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("WhatsAppSender")

# WhatsApp API Configuration
WHATSAPP_API_VERSION = "v18.0"
WHATSAPP_API_BASE = f"https://graph.facebook.com/{WHATSAPP_API_VERSION}"


class WhatsAppSender:
    """Handles sending WhatsApp messages via Business API."""
    
    def __init__(self, dry_run: bool = False):
        """
        Initialize WhatsApp Sender.
        
        Args:
            dry_run: If True, simulate sending without actual API calls
        """
        self.dry_run = dry_run
        
        if not dry_run:
            self.phone_number_id = get_env_var("WHATSAPP_PHONE_NUMBER_ID")
            self.access_token = get_env_var("WHATSAPP_ACCESS_TOKEN")
        else:
            self.phone_number_id = "DRY_RUN_PHONE_ID"
            self.access_token = "DRY_RUN_TOKEN"
            logger.info("🔵 DRY RUN MODE - No actual messages will be sent")
    
    def send_text_message(self, to: str, message: str) -> bool:
        """
        Sends a text message via WhatsApp.
        
        Args:
            to: Recipient phone number (with country code, e.g., +1234567890)
            message: Message text
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate phone number format
            if not to.startswith('+'):
                logger.warning(f"Phone number should start with +. Adding + prefix.")
                to = f"+{to}"
            
            # Validate message length
            if not validate_text_length(message, 'WHATSAPP'):
                return False
            
            if self.dry_run:
                logger.info(f"[DRY RUN] Would send WhatsApp message:")
                logger.info(f"To: {to}")
                logger.info(f"Message: {message[:100]}...")
                return True
            
            # Prepare API request
            url = f"{WHATSAPP_API_BASE}/{self.phone_number_id}/messages"
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "messaging_product": "whatsapp",
                "to": to.replace('+', ''),  # Remove + for API
                "type": "text",
                "text": {
                    "body": message
                }
            }
            
            # Make API call
            logger.info(f"Sending WhatsApp message to {to}...")
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            message_id = result.get("messages", [{}])[0].get("id")
            
            logger.info(f"✅ Message sent successfully! Message ID: {message_id}")
            
            # Log to social media posts
            log_social_post(
                platform="WHATSAPP",
                status="SUCCESS",
                details={
                    "message_id": message_id,
                    "to": to,
                    "message_preview": message[:100]
                }
            )
            
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ WhatsApp API error: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            
            log_social_post(
                platform="WHATSAPP",
                status="FAILURE",
                details={"error": str(e), "to": to}
            )
            return False
            
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}", exc_info=True)
            log_social_post(
                platform="WHATSAPP",
                status="FAILURE",
                details={"error": str(e)}
            )
            return False
    
    def send_template_message(
        self,
        to: str,
        template_name: str,
        parameters: list = None
    ) -> bool:
        """
        Sends a template message via WhatsApp.
        
        Template messages are required for proactive outreach (outside 24-hour window).
        
        Args:
            to: Recipient phone number
            template_name: Approved template name
            parameters: List of parameter values for template
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.dry_run:
                logger.info(f"[DRY RUN] Would send WhatsApp template message:")
                logger.info(f"To: {to}")
                logger.info(f"Template: {template_name}")
                logger.info(f"Parameters: {parameters}")
                return True
            
            # Prepare API request
            url = f"{WHATSAPP_API_BASE}/{self.phone_number_id}/messages"
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            # Build template components
            components = []
            if parameters:
                components.append({
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": str(param)}
                        for param in parameters
                    ]
                })
            
            payload = {
                "messaging_product": "whatsapp",
                "to": to.replace('+', ''),
                "type": "template",
                "template": {
                    "name": template_name,
                    "language": {"code": "en"},
                    "components": components
                }
            }
            
            # Make API call
            logger.info(f"Sending WhatsApp template message to {to}...")
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            message_id = result.get("messages", [{}])[0].get("id")
            
            logger.info(f"✅ Template message sent! Message ID: {message_id}")
            
            # Log to social media posts
            log_social_post(
                platform="WHATSAPP",
                status="SUCCESS",
                details={
                    "message_id": message_id,
                    "to": to,
                    "template": template_name,
                    "type": "template"
                }
            )
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error sending template message: {e}", exc_info=True)
            log_social_post(
                platform="WHATSAPP",
                status="FAILURE",
                details={"error": str(e), "type": "template"}
            )
            return False


def parse_content(content: str) -> dict:
    """
    Parses markdown content to extract WhatsApp message details.
    
    Expected format:
        **To:** +1234567890
        
        **Message:**
        Message text here
        
        **Template:** (optional, for proactive messages)
        order_confirmation
        
        **Template Parameters:** (optional)
        - Order ID: 12345
        - Amount: $99.99
    
    Args:
        content: Markdown content
        
    Returns:
        Dict with parsed fields
    """
    to = parse_markdown_field(content, "To")
    message = parse_markdown_field(content, "Message")
    template = parse_markdown_field(content, "Template")
    
    # Parse template parameters
    params = []
    param_list = parse_markdown_list(content, "Template Parameters")
    if param_list:
        # Extract values from "Key: Value" format
        for item in param_list:
            if ':' in item:
                value = item.split(':', 1)[1].strip()
                params.append(value)
            else:
                params.append(item)
    
    return {
        "to": to,
        "message": message,
        "template": template,
        "parameters": params if params else None
    }


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description="Send WhatsApp message")
    parser.add_argument("content", help="Message content (markdown format)")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without sending")
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("WhatsApp Sender Started")
    logger.info("=" * 60)
    
    try:
        # Parse content
        parsed = parse_content(args.content)
        to = parsed["to"]
        message = parsed["message"]
        template = parsed["template"]
        parameters = parsed["parameters"]
        
        if not to:
            logger.error("No recipient phone number found")
            return False
        
        # Initialize sender
        sender = WhatsAppSender(dry_run=args.dry_run)
        
        # Send based on content type
        if template:
            logger.info(f"Detected template message: {template}")
            success = sender.send_template_message(to, template, parameters)
        elif message:
            logger.info("Detected text message")
            success = sender.send_text_message(to, message)
        else:
            logger.error("No message content found")
            return False
        
        if success:
            logger.info("✅ WhatsApp sending completed successfully")
            return True
        else:
            logger.error("❌ WhatsApp sending failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

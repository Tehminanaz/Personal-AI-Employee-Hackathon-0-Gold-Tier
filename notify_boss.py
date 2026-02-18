#!/usr/bin/env python3
"""
Notify Boss - Mobile Notification Skill
Sends push notifications to the boss's phone via ntfy.sh.

Topic: ntfy.sh/kashan_sentinel_2026

Usage:
    python notify_boss.py "Message Content"
    import notify_boss; notify_boss.send_notification("Message")
"""

import sys
import requests
import logging

# Configuration
NTFY_TOPIC = "kashan_sentinel_2026"
NTFY_URL = f"https://ntfy.sh/{NTFY_TOPIC}"

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("NotifyBoss")

def send_notification(message: str, title: str = "Digital FTE Sentinel", priority: str = "default"):
    """
    Sends a push notification to ntfy.sh.
    
    Args:
        message: The content of the notification
        title: Title of the notification (default: Digital FTE Sentinel)
        priority: Priority level (urgent, high, default, low, min)
    """
    try:
        headers = {
            "Title": title,
            "Priority": priority
        }
        
        response = requests.post(
            NTFY_URL,
            data=message.encode('utf-8'),
            headers=headers
        )
        
        if response.status_code == 200:
            logger.info(f"Notification sent: {message}")
            return True
        else:
            logger.error(f"Failed to send notification. Status: {response.status_code}, Body: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending notification: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        msg = " ".join(sys.argv[1:])
        send_notification(msg)
    else:
        print("Usage: python notify_boss.py 'Message Content'")

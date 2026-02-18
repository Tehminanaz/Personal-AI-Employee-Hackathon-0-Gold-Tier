#!/usr/bin/env python3
"""
Facebook Poster - Digital FTE System
Posts content to Facebook Page using Graph API.

Usage:
    python facebook_poster.py "content"
    python facebook_poster.py "content" --dry-run

Environment Variables Required:
    FACEBOOK_PAGE_ACCESS_TOKEN
    FACEBOOK_PAGE_ID
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
        validate_image_url,
        download_image,
        log_social_post,
        get_env_var,
        validate_text_length
    )
    from social_media_summary import add_post_summary
except ImportError:
    print("Error: social_media_utils.py or social_media_summary.py not found")
    sys.exit(1)

# Load environment variables
load_dotenv()

# Configuration
BASE_DIR = Path(__file__).parent.resolve()
LOGS_DIR = BASE_DIR / "Logs"
LOGS_DIR.mkdir(exist_ok=True)

# Logging setup
LOG_FILE = LOGS_DIR / "facebook_poster.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("FacebookPoster")

# Facebook Graph API Configuration
GRAPH_API_VERSION = "v18.0"
GRAPH_API_BASE = f"https://graph.facebook.com/{GRAPH_API_VERSION}"


class FacebookPoster:
    """Handles posting to Facebook Page."""
    
    def __init__(self, dry_run: bool = False, generate_summary: bool = False):
        """
        Initialize Facebook Poster.
        
        Args:
            dry_run: If True, simulate posting without actual API calls
            generate_summary: If True, add post to summary file
        """
        self.dry_run = dry_run
        self.generate_summary = generate_summary
        
        if not dry_run:
            self.access_token = get_env_var("FACEBOOK_PAGE_ACCESS_TOKEN")
            self.page_id = get_env_var("FACEBOOK_PAGE_ID")
        else:
            self.access_token = "DRY_RUN_TOKEN"
            self.page_id = "DRY_RUN_PAGE_ID"
            logger.info("🔵 DRY RUN MODE - No actual posts will be made")
    
    def post_text(self, message: str, link: str = None) -> bool:
        """
        Posts text (and optional link) to Facebook Page.
        
        Args:
            message: Post message
            link: Optional URL to share
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate message length
            if not validate_text_length(message, 'FACEBOOK'):
                return False
            
            if self.dry_run:
                logger.info(f"[DRY RUN] Would post to Facebook:")
                logger.info(f"Message: {message[:100]}...")
                if link:
                    logger.info(f"Link: {link}")
                return True
            
            # Prepare API request
            url = f"{GRAPH_API_BASE}/{self.page_id}/feed"
            
            payload = {
                "message": message,
                "access_token": self.access_token
            }
            
            if link:
                payload["link"] = link
            
            # Make API call
            logger.info("Posting to Facebook Page...")
            response = requests.post(url, data=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            post_id = result.get("id")
            
            logger.info(f"✅ Posted successfully! Post ID: {post_id}")
            
            # Log to social media posts
            log_social_post(
                platform="FACEBOOK",
                status="SUCCESS",
                details={
                    "post_id": post_id,
                    "message_preview": message[:100],
                    "link": link
                }
            )
            
            # Add to summary if requested
            if self.generate_summary:
                add_post_summary(
                    platform="FACEBOOK",
                    post_id=post_id,
                    content_preview=message[:80],
                    post_type="text",
                    metrics={"link": link if link else "None"}
                )
            
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Facebook API error: {e}")
            if hasattr(e.response, 'text'):
                logger.error(f"Response: {e.response.text}")
            
            log_social_post(
                platform="FACEBOOK",
                status="FAILURE",
                details={"error": str(e)}
            )
            return False
            
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}", exc_info=True)
            log_social_post(
                platform="FACEBOOK",
                status="FAILURE",
                details={"error": str(e)}
            )
            return False
    
    def post_photo(self, image_url: str, caption: str = "") -> bool:
        """
        Posts a photo to Facebook Page.
        
        Args:
            image_url: URL of image to post
            caption: Optional caption
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate image URL
            if not validate_image_url(image_url):
                logger.error("Invalid image URL")
                return False
            
            if self.dry_run:
                logger.info(f"[DRY RUN] Would post photo to Facebook:")
                logger.info(f"Image: {image_url}")
                logger.info(f"Caption: {caption[:100]}...")
                return True
            
            # Prepare API request
            url = f"{GRAPH_API_BASE}/{self.page_id}/photos"
            
            payload = {
                "url": image_url,
                "caption": caption,
                "access_token": self.access_token
            }
            
            # Make API call
            logger.info("Posting photo to Facebook Page...")
            response = requests.post(url, data=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            post_id = result.get("id")
            
            logger.info(f"✅ Photo posted successfully! Post ID: {post_id}")
            
            # Log to social media posts
            log_social_post(
                platform="FACEBOOK",
                status="SUCCESS",
                details={
                    "post_id": post_id,
                    "type": "photo",
                    "image_url": image_url,
                    "caption_preview": caption[:100]
                }
            )
            
            # Add to summary if requested
            if self.generate_summary:
                add_post_summary(
                    platform="FACEBOOK",
                    post_id=post_id,
                    content_preview=caption[:80],
                    post_type="photo",
                    metrics={"image_url": image_url}
                )
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error posting photo: {e}", exc_info=True)
            log_social_post(
                platform="FACEBOOK",
                status="FAILURE",
                details={"error": str(e), "type": "photo"}
            )
            return False


def parse_content(content: str) -> dict:
    """
    Parses markdown content to extract Facebook post details.
    
    Expected format:
        **Message:**
        Post content here
        
        **Link:** (optional)
        https://example.com
        
        **Image URL:** (optional)
        https://example.com/image.jpg
    
    Args:
        content: Markdown content
        
    Returns:
        Dict with parsed fields
    """
    message = parse_markdown_field(content, "Message")
    link = parse_markdown_field(content, "Link")
    image_url = parse_markdown_field(content, "Image URL")
    
    # If no structured fields, use entire content as message
    if not message:
        message = content.strip()
    
    return {
        "message": message,
        "link": link,
        "image_url": image_url
    }


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description="Post to Facebook Page")
    parser.add_argument("content", help="Post content (markdown format)")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without posting")
    parser.add_argument("--summary", action="store_true", help="Generate post summary")
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("Facebook Poster Started")
    logger.info("=" * 60)
    
    try:
        # Parse content
        parsed = parse_content(args.content)
        message = parsed["message"]
        link = parsed["link"]
        image_url = parsed["image_url"]
        
        if not message:
            logger.error("No message content found")
            return False
        
        # Initialize poster
        poster = FacebookPoster(dry_run=args.dry_run, generate_summary=args.summary)
        
        # Post based on content type
        if image_url:
            success = poster.post_photo(image_url, caption=message)
        else:
            success = poster.post_text(message, link=link)
        
        if success:
            logger.info("✅ Facebook posting completed successfully")
            return True
        else:
            logger.error("❌ Facebook posting failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

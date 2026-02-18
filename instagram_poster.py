#!/usr/bin/env python3
"""
Instagram Poster - Digital FTE System
Posts photos to Instagram using Instagram Graph API.

Usage:
    python instagram_poster.py "content"
    python instagram_poster.py "content" --dry-run

Environment Variables Required:
    INSTAGRAM_ACCESS_TOKEN
    INSTAGRAM_BUSINESS_ACCOUNT_ID

Note: Instagram requires Business or Creator account linked to Facebook Page.
"""

import os
import sys
import logging
import argparse
import requests
import time
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Import shared utilities
try:
    from social_media_utils import (
        parse_markdown_field,
        validate_image_url,
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
LOG_FILE = LOGS_DIR / "instagram_poster.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("InstagramPoster")

# Instagram Graph API Configuration
GRAPH_API_VERSION = "v18.0"
GRAPH_API_BASE = f"https://graph.facebook.com/{GRAPH_API_VERSION}"


class InstagramPoster:
    """Handles posting to Instagram via Graph API."""
    
    def __init__(self, dry_run: bool = False, generate_summary: bool = False):
        """
        Initialize Instagram Poster.
        
        Args:
            dry_run: If True, simulate posting without actual API calls
            generate_summary: If True, add post to summary file
        """
        self.dry_run = dry_run
        self.generate_summary = generate_summary
        
        if not dry_run:
            self.access_token = get_env_var("INSTAGRAM_ACCESS_TOKEN")
            self.account_id = get_env_var("INSTAGRAM_BUSINESS_ACCOUNT_ID")
        else:
            self.access_token = "DRY_RUN_TOKEN"
            self.account_id = "DRY_RUN_ACCOUNT_ID"
            logger.info("🔵 DRY RUN MODE - No actual posts will be made")
    
    def post_photo(self, image_url: str, caption: str = "") -> bool:
        """
        Posts a photo to Instagram.
        
        Instagram posting is a 2-step process:
        1. Create media container
        2. Publish the container
        
        Args:
            image_url: Publicly accessible image URL
            caption: Photo caption (max 2200 characters)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate image URL
            if not validate_image_url(image_url):
                logger.error("Invalid image URL")
                return False
            
            # Validate caption length
            if not validate_text_length(caption, 'INSTAGRAM'):
                return False
            
            if self.dry_run:
                logger.info(f"[DRY RUN] Would post to Instagram:")
                logger.info(f"Image: {image_url}")
                logger.info(f"Caption: {caption[:100]}...")
                return True
            
            # Step 1: Create media container
            logger.info("Creating Instagram media container...")
            container_id = self._create_media_container(image_url, caption)
            
            if not container_id:
                logger.error("Failed to create media container")
                return False
            
            # Step 2: Publish the container
            logger.info(f"Publishing media container {container_id}...")
            post_id = self._publish_media(container_id)
            
            if not post_id:
                logger.error("Failed to publish media")
                return False
            
            logger.info(f"✅ Photo posted successfully! Post ID: {post_id}")
            
            # Log to social media posts
            log_social_post(
                platform="INSTAGRAM",
                status="SUCCESS",
                details={
                    "post_id": post_id,
                    "image_url": image_url,
                    "caption_preview": caption[:100]
                }
            )
            
            # Add to summary if requested
            if self.generate_summary:
                add_post_summary(
                    platform="INSTAGRAM",
                    post_id=post_id,
                    content_preview=caption[:80],
                    post_type="photo",
                    metrics={"image_url": image_url}
                )
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error posting to Instagram: {e}", exc_info=True)
            log_social_post(
                platform="INSTAGRAM",
                status="FAILURE",
                details={"error": str(e)}
            )
            return False
    
    def _create_media_container(self, image_url: str, caption: str) -> str:
        """
        Creates an Instagram media container.
        
        Args:
            image_url: Image URL
            caption: Caption text
            
        Returns:
            Container ID if successful, None otherwise
        """
        try:
            url = f"{GRAPH_API_BASE}/{self.account_id}/media"
            
            params = {
                "image_url": image_url,
                "caption": caption,
                "access_token": self.access_token
            }
            
            response = requests.post(url, params=params, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            container_id = result.get("id")
            
            logger.info(f"Media container created: {container_id}")
            return container_id
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API error creating container: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            return None
    
    def _publish_media(self, container_id: str) -> str:
        """
        Publishes an Instagram media container.
        
        Args:
            container_id: Container ID from create step
            
        Returns:
            Post ID if successful, None otherwise
        """
        try:
            # Wait a moment for media to be processed
            time.sleep(2)
            
            url = f"{GRAPH_API_BASE}/{self.account_id}/media_publish"
            
            params = {
                "creation_id": container_id,
                "access_token": self.access_token
            }
            
            response = requests.post(url, params=params, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            post_id = result.get("id")
            
            logger.info(f"Media published: {post_id}")
            return post_id
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API error publishing media: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            return None


def parse_content(content: str) -> dict:
    """
    Parses markdown content to extract Instagram post details.
    
    Expected format:
        **Image URL:**
        https://example.com/photo.jpg
        
        **Caption:**
        Photo caption with #hashtags
        
        **Location:** (optional)
        New York, NY
    
    Args:
        content: Markdown content
        
    Returns:
        Dict with parsed fields
    """
    image_url = parse_markdown_field(content, "Image URL")
    caption = parse_markdown_field(content, "Caption")
    location = parse_markdown_field(content, "Location")
    
    # If no caption, use content as caption
    if not caption:
        caption = content.strip()
    
    return {
        "image_url": image_url,
        "caption": caption,
        "location": location
    }


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description="Post to Instagram")
    parser.add_argument("content", help="Post content (markdown format)")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without posting")
    parser.add_argument("--summary", action="store_true", help="Generate post summary")
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("Instagram Poster Started")
    logger.info("=" * 60)
    
    try:
        # Parse content
        parsed = parse_content(args.content)
        image_url = parsed["image_url"]
        caption = parsed["caption"]
        
        if not image_url:
            logger.error("No image URL found")
            return False
        
        # Initialize poster
        poster = InstagramPoster(dry_run=args.dry_run, generate_summary=args.summary)
        
        # Post photo
        success = poster.post_photo(image_url, caption)
        
        if success:
            logger.info("✅ Instagram posting completed successfully")
            return True
        else:
            logger.error("❌ Instagram posting failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

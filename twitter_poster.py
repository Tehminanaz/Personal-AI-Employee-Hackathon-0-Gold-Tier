#!/usr/bin/env python3
"""
Twitter Poster - Digital FTE System
Posts tweets to Twitter/X using Twitter API v2.

Usage:
    python twitter_poster.py "content"
    python twitter_poster.py "content" --dry-run

Environment Variables Required:
    TWITTER_API_KEY
    TWITTER_API_SECRET
    TWITTER_ACCESS_TOKEN
    TWITTER_ACCESS_SECRET
"""

import os
import sys
import logging
import argparse
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Import tweepy for Twitter API
try:
    import tweepy
except ImportError:
    print("Error: tweepy not installed. Run: pip install tweepy")
    sys.exit(1)

# Import shared utilities
try:
    from social_media_utils import (
        parse_markdown_field,
        parse_markdown_list,
        truncate_text,
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
LOG_FILE = LOGS_DIR / "twitter_poster.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("TwitterPoster")

# Twitter limits
TWITTER_CHAR_LIMIT = 280


class TwitterPoster:
    """Handles posting to Twitter/X."""
    
    def __init__(self, dry_run: bool = False, generate_summary: bool = False):
        """
        Initialize Twitter Poster.
        
        Args:
            dry_run: If True, simulate posting without actual API calls
            generate_summary: If True, add post to summary file
        """
        self.dry_run = dry_run
        self.generate_summary = generate_summary
        self.client = None
        
        if not dry_run:
            try:
                # Get credentials
                api_key = get_env_var("TWITTER_API_KEY")
                api_secret = get_env_var("TWITTER_API_SECRET")
                access_token = get_env_var("TWITTER_ACCESS_TOKEN")
                access_secret = get_env_var("TWITTER_ACCESS_SECRET")
                
                # Initialize Tweepy client (API v2)
                self.client = tweepy.Client(
                    consumer_key=api_key,
                    consumer_secret=api_secret,
                    access_token=access_token,
                    access_token_secret=access_secret
                )
                
                logger.info("✅ Twitter API authenticated")
                
            except Exception as e:
                logger.error(f"❌ Twitter authentication failed: {e}")
                raise
        else:
            logger.info("🔵 DRY RUN MODE - No actual tweets will be posted")
    
    def post_tweet(self, text: str) -> bool:
        """
        Posts a single tweet.
        
        Args:
            text: Tweet text (max 280 characters)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate length
            if len(text) > TWITTER_CHAR_LIMIT:
                logger.warning(f"Tweet too long ({len(text)} chars), truncating...")
                text = truncate_text(text, TWITTER_CHAR_LIMIT)
            
            if self.dry_run:
                logger.info(f"[DRY RUN] Would post tweet:")
                logger.info(f"Text: {text}")
                logger.info(f"Length: {len(text)} characters")
                return True
            
            # Post tweet
            logger.info("Posting tweet...")
            response = self.client.create_tweet(text=text)
            
            tweet_id = response.data['id']
            logger.info(f"✅ Tweet posted successfully! ID: {tweet_id}")
            
            # Log to social media posts
            log_social_post(
                platform="TWITTER",
                status="SUCCESS",
                details={
                    "tweet_id": tweet_id,
                    "text": text,
                    "length": len(text)
                }
            )
            
            # Add to summary if requested
            if self.generate_summary:
                add_post_summary(
                    platform="TWITTER",
                    post_id=tweet_id,
                    content_preview=text[:80],
                    post_type="tweet",
                    metrics={"length": len(text)}
                )
            
            return True
            
        except tweepy.TweepyException as e:
            logger.error(f"❌ Twitter API error: {e}")
            log_social_post(
                platform="TWITTER",
                status="FAILURE",
                details={"error": str(e)}
            )
            return False
            
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}", exc_info=True)
            log_social_post(
                platform="TWITTER",
                status="FAILURE",
                details={"error": str(e)}
            )
            return False
    
    def post_thread(self, tweets: list) -> bool:
        """
        Posts a thread of tweets.
        
        Args:
            tweets: List of tweet texts
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.dry_run:
                logger.info(f"[DRY RUN] Would post thread with {len(tweets)} tweets:")
                for i, tweet in enumerate(tweets, 1):
                    logger.info(f"  {i}. {tweet[:50]}... ({len(tweet)} chars)")
                return True
            
            logger.info(f"Posting thread with {len(tweets)} tweets...")
            
            previous_tweet_id = None
            tweet_ids = []
            
            for i, text in enumerate(tweets, 1):
                # Truncate if needed
                if len(text) > TWITTER_CHAR_LIMIT:
                    text = truncate_text(text, TWITTER_CHAR_LIMIT)
                
                # Post tweet (reply to previous if thread)
                if previous_tweet_id:
                    response = self.client.create_tweet(
                        text=text,
                        in_reply_to_tweet_id=previous_tweet_id
                    )
                else:
                    response = self.client.create_tweet(text=text)
                
                tweet_id = response.data['id']
                tweet_ids.append(tweet_id)
                previous_tweet_id = tweet_id
                
                logger.info(f"  ✅ Tweet {i}/{len(tweets)} posted (ID: {tweet_id})")
            
            logger.info(f"✅ Thread posted successfully! {len(tweet_ids)} tweets")
            
            # Log to social media posts
            log_social_post(
                platform="TWITTER",
                status="SUCCESS",
                details={
                    "type": "thread",
                    "tweet_count": len(tweet_ids),
                    "tweet_ids": tweet_ids
                }
            )
            
            # Add to summary if requested
            if self.generate_summary:
                add_post_summary(
                    platform="TWITTER",
                    post_id=tweet_ids[0],  # First tweet ID
                    content_preview=tweets[0][:80],
                    post_type="thread",
                    metrics={"tweet_count": len(tweet_ids)}
                )
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error posting thread: {e}", exc_info=True)
            log_social_post(
                platform="TWITTER",
                status="FAILURE",
                details={"error": str(e), "type": "thread"}
            )
            return False


def parse_content(content: str) -> dict:
    """
    Parses markdown content to extract tweet details.
    
    Expected format:
        **Tweet:**
        Single tweet text
        
        OR
        
        **Thread:**
        1. First tweet
        2. Second tweet
        3. Third tweet
    
    Args:
        content: Markdown content
        
    Returns:
        Dict with parsed fields
    """
    # Check for single tweet
    tweet = parse_markdown_field(content, "Tweet")
    
    # Check for thread
    thread = parse_markdown_list(content, "Thread")
    
    # If no structured fields, use entire content as single tweet
    if not tweet and not thread:
        tweet = content.strip()
    
    return {
        "tweet": tweet,
        "thread": thread
    }


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description="Post to Twitter/X")
    parser.add_argument("content", help="Tweet content (markdown format)")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without posting")
    parser.add_argument("--summary", action="store_true", help="Generate post summary")
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("Twitter Poster Started")
    logger.info("=" * 60)
    
    try:
        # Parse content
        parsed = parse_content(args.content)
        tweet = parsed["tweet"]
        thread = parsed["thread"]
        
        # Initialize poster
        poster = TwitterPoster(dry_run=args.dry_run, generate_summary=args.summary)
        
        # Post based on content type
        if thread:
            logger.info(f"Detected thread with {len(thread)} tweets")
            success = poster.post_thread(thread)
        elif tweet:
            logger.info("Detected single tweet")
            success = poster.post_tweet(tweet)
        else:
            logger.error("No tweet content found")
            return False
        
        if success:
            logger.info("✅ Twitter posting completed successfully")
            return True
        else:
            logger.error("❌ Twitter posting failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

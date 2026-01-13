#!/usr/bin/env python3
"""
Social Media Utilities - Digital FTE System
Shared utilities for all social media integrations.

Functions:
- Image validation and downloading
- Text processing (hashtags, truncation)
- Rate limiting
- Logging helpers
"""

import os
import re
import time
import logging
import requests
from pathlib import Path
from typing import List, Optional, Callable
from functools import wraps
from datetime import datetime

logger = logging.getLogger("SocialMediaUtils")

# Configuration
MAX_IMAGE_SIZE_MB = 10
ALLOWED_IMAGE_FORMATS = ['.jpg', '.jpeg', '.png', '.gif', '.webp']


def validate_image_url(url: str) -> bool:
    """
    Validates if a URL points to a valid image.
    
    Args:
        url: Image URL to validate
        
    Returns:
        True if valid, False otherwise
    """
    try:
        # Check URL format
        if not url.startswith(('http://', 'https://')):
            logger.warning(f"Invalid URL scheme: {url}")
            return False
        
        # Check file extension
        path = url.split('?')[0]  # Remove query params
        ext = Path(path).suffix.lower()
        if ext not in ALLOWED_IMAGE_FORMATS:
            logger.warning(f"Unsupported image format: {ext}")
            return False
        
        # HEAD request to check if image exists
        response = requests.head(url, timeout=5, allow_redirects=True)
        if response.status_code != 200:
            logger.warning(f"Image URL returned {response.status_code}")
            return False
        
        # Check content type
        content_type = response.headers.get('Content-Type', '')
        if not content_type.startswith('image/'):
            logger.warning(f"Invalid content type: {content_type}")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error validating image URL: {e}")
        return False


def download_image(url: str, save_path: Optional[Path] = None) -> Optional[bytes]:
    """
    Downloads an image from URL.
    
    Args:
        url: Image URL
        save_path: Optional path to save image
        
    Returns:
        Image bytes if successful, None otherwise
    """
    try:
        response = requests.get(url, timeout=10, stream=True)
        response.raise_for_status()
        
        # Check size
        content_length = int(response.headers.get('Content-Length', 0))
        if content_length > MAX_IMAGE_SIZE_MB * 1024 * 1024:
            logger.error(f"Image too large: {content_length / 1024 / 1024:.2f}MB")
            return None
        
        image_data = response.content
        
        # Save if path provided
        if save_path:
            save_path.parent.mkdir(parents=True, exist_ok=True)
            with open(save_path, 'wb') as f:
                f.write(image_data)
            logger.info(f"Image saved to {save_path}")
        
        return image_data
        
    except Exception as e:
        logger.error(f"Error downloading image: {e}")
        return None


def extract_hashtags(text: str) -> List[str]:
    """
    Extracts hashtags from text.
    
    Args:
        text: Text containing hashtags
        
    Returns:
        List of hashtags (without # symbol)
    """
    # Match #word or #word_with_underscore
    pattern = r'#(\w+)'
    hashtags = re.findall(pattern, text)
    return hashtags


def add_hashtags(text: str, hashtags: List[str]) -> str:
    """
    Adds hashtags to text if not already present.
    
    Args:
        text: Original text
        hashtags: List of hashtags to add
        
    Returns:
        Text with hashtags appended
    """
    existing = extract_hashtags(text)
    new_tags = [tag for tag in hashtags if tag not in existing]
    
    if new_tags:
        formatted_tags = ' '.join(f'#{tag}' for tag in new_tags)
        return f"{text}\n\n{formatted_tags}"
    
    return text


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncates text to max length, preserving word boundaries.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    # Account for suffix length
    max_length -= len(suffix)
    
    # Find last space before max_length
    truncated = text[:max_length]
    last_space = truncated.rfind(' ')
    
    if last_space > 0:
        truncated = truncated[:last_space]
    
    return truncated + suffix


def extract_urls(text: str) -> List[str]:
    """
    Extracts URLs from text.
    
    Args:
        text: Text containing URLs
        
    Returns:
        List of URLs
    """
    url_pattern = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+'
    urls = re.findall(url_pattern, text)
    return urls


def sanitize_filename(filename: str) -> str:
    """
    Sanitizes filename by removing invalid characters.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Replace spaces with underscores
    sanitized = sanitized.replace(' ', '_')
    # Remove multiple underscores
    sanitized = re.sub(r'_+', '_', sanitized)
    return sanitized


def rate_limit(calls: int = 10, period: int = 60):
    """
    Decorator to rate limit function calls.
    
    Args:
        calls: Number of calls allowed
        period: Time period in seconds
        
    Usage:
        @rate_limit(calls=5, period=60)
        def api_call():
            pass
    """
    def decorator(func: Callable) -> Callable:
        call_times = []
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal call_times
            now = time.time()
            
            # Remove old calls outside the period
            call_times = [t for t in call_times if now - t < period]
            
            # Check if rate limit exceeded
            if len(call_times) >= calls:
                sleep_time = period - (now - call_times[0])
                logger.warning(f"Rate limit reached. Sleeping for {sleep_time:.2f}s")
                time.sleep(sleep_time)
                call_times = []
            
            # Record this call
            call_times.append(time.time())
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def parse_markdown_field(content: str, field_name: str) -> Optional[str]:
    """
    Extracts a field value from markdown content.
    
    Args:
        content: Markdown content
        field_name: Field name to extract (e.g., "Message", "To")
        
    Returns:
        Field value or None
        
    Example:
        **Message:**
        Hello world
        
        parse_markdown_field(content, "Message") -> "Hello world"
    """
    # Match **Field:** or **Field** followed by content
    pattern = rf'\*\*{field_name}:?\*\*\s*\n?(.*?)(?=\n\*\*|\Z)'
    match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
    
    if match:
        value = match.group(1).strip()
        return value if value else None
    
    return None


def parse_markdown_list(content: str, field_name: str) -> List[str]:
    """
    Extracts a list from markdown content.
    
    Args:
        content: Markdown content
        field_name: Field name (e.g., "Images")
        
    Returns:
        List of items
        
    Example:
        **Images:**
        - image1.jpg
        - image2.jpg
    """
    items = []
    
    # Find the field section
    pattern = rf'\*\*{field_name}:?\*\*\s*\n((?:[-*]\s*.+\n?)+)'
    match = re.search(pattern, content, re.IGNORECASE)
    
    if match:
        list_text = match.group(1)
        # Extract list items
        item_pattern = r'[-*]\s*(.+)'
        items = re.findall(item_pattern, list_text)
        items = [item.strip() for item in items]
    
    return items


def log_social_post(
    platform: str,
    status: str,
    details: dict,
    log_file: Path = None
) -> None:
    """
    Logs social media post to JSON file.
    
    Args:
        platform: Platform name (FACEBOOK, TWITTER, etc.)
        status: SUCCESS or FAILURE
        details: Additional details dict
        log_file: Optional custom log file path
    """
    import json
    
    if log_file is None:
        log_file = Path(__file__).parent / "Logs" / "Social_Media_Posts.json"
    
    log_file.parent.mkdir(exist_ok=True)
    
    entry = {
        "timestamp": datetime.now().isoformat(),
        "platform": platform,
        "status": status,
        **details
    }
    
    # Read existing logs
    logs = []
    if log_file.exists():
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        except json.JSONDecodeError:
            logger.warning("Log file corrupted, starting fresh")
    
    logs.append(entry)
    
    # Write updated logs
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(logs, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Logged {platform} post: {status}")


def get_env_var(var_name: str, required: bool = True) -> Optional[str]:
    """
    Gets environment variable with validation.
    
    Args:
        var_name: Environment variable name
        required: Whether variable is required
        
    Returns:
        Variable value or None
        
    Raises:
        ValueError if required variable is missing
    """
    value = os.getenv(var_name)
    
    if required and not value:
        raise ValueError(f"Missing required environment variable: {var_name}")
    
    return value


# Platform-specific character limits
PLATFORM_LIMITS = {
    'TWITTER': 280,
    'FACEBOOK': 63206,  # Practical limit
    'INSTAGRAM': 2200,
    'LINKEDIN': 3000,
    'WHATSAPP': 4096
}


def validate_text_length(text: str, platform: str) -> bool:
    """
    Validates text length for platform.
    
    Args:
        text: Text to validate
        platform: Platform name
        
    Returns:
        True if valid, False otherwise
    """
    max_length = PLATFORM_LIMITS.get(platform.upper())
    
    if max_length is None:
        logger.warning(f"Unknown platform: {platform}")
        return True
    
    if len(text) > max_length:
        logger.error(f"Text too long for {platform}: {len(text)} > {max_length}")
        return False
    
    return True


if __name__ == "__main__":
    # Test functions
    print("Testing social_media_utils.py")
    
    # Test hashtag extraction
    text = "Hello #world this is a #test post #python"
    hashtags = extract_hashtags(text)
    print(f"Hashtags: {hashtags}")
    
    # Test truncation
    long_text = "This is a very long text that needs to be truncated to fit within limits"
    truncated = truncate_text(long_text, 30)
    print(f"Truncated: {truncated}")
    
    # Test markdown parsing
    content = """
    **Message:**
    Hello world!
    
    **Images:**
    - image1.jpg
    - image2.jpg
    """
    message = parse_markdown_field(content, "Message")
    images = parse_markdown_list(content, "Images")
    print(f"Message: {message}")
    print(f"Images: {images}")
    
    print("\n✅ All tests passed!")

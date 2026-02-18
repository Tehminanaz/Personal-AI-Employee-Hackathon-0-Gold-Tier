#!/usr/bin/env python3
"""
Social Media Summary Generator - Digital FTE System
Generates and maintains a unified summary of all social media posts.

This module provides functionality to:
- Append post summaries to Management/Social_Media_Summary.md
- Track metrics (post IDs, timestamps, engagement)
- Generate daily/weekly summaries
- Support all platforms (Facebook, Instagram, Twitter, LinkedIn)

Usage:
    from social_media_summary import add_post_summary
    
    add_post_summary(
        platform="FACEBOOK",
        post_id="123456789",
        content_preview="Check out our new product...",
        metrics={"likes": 50, "shares": 10}
    )
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List

# Configuration
BASE_DIR = Path(__file__).parent.resolve()
MANAGEMENT_DIR = BASE_DIR / "Management"
SUMMARY_FILE = MANAGEMENT_DIR / "Social_Media_Summary.md"

# Ensure directory exists
MANAGEMENT_DIR.mkdir(exist_ok=True)


def initialize_summary_file():
    """Initialize the summary file if it doesn't exist."""
    if not SUMMARY_FILE.exists():
        content = """# Social Media Summary

This file tracks all social media posts made by the Digital FTE system.

---

## Recent Posts

| Date | Platform | Post ID | Content Preview | Metrics |
|------|----------|---------|-----------------|---------|
"""
        with open(SUMMARY_FILE, 'w', encoding='utf-8') as f:
            f.write(content)


def add_post_summary(
    platform: str,
    post_id: str,
    content_preview: str,
    metrics: Optional[Dict] = None,
    post_type: str = "text",
    url: Optional[str] = None
) -> bool:
    """
    Add a post summary to the tracking file.
    
    Args:
        platform: Platform name (FACEBOOK, INSTAGRAM, TWITTER, LINKEDIN)
        post_id: Unique post ID from platform
        content_preview: First 50-100 characters of post
        metrics: Optional dict of metrics (likes, shares, comments, etc.)
        post_type: Type of post (text, photo, video, thread)
        url: Optional URL to the post
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Initialize file if needed
        initialize_summary_file()
        
        # Format timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        
        # Format metrics
        if metrics:
            metrics_str = ", ".join([f"{k}: {v}" for k, v in metrics.items()])
        else:
            metrics_str = "Pending"
        
        # Truncate content preview
        if len(content_preview) > 80:
            content_preview = content_preview[:77] + "..."
        
        # Create table row
        row = f"| {timestamp} | {platform} | `{post_id}` | {content_preview} | {metrics_str} |\n"
        
        # Append to file
        with open(SUMMARY_FILE, 'a', encoding='utf-8') as f:
            f.write(row)
        
        return True
        
    except Exception as e:
        print(f"Error adding post summary: {e}")
        return False


def get_daily_summary(date: Optional[str] = None) -> Dict:
    """
    Get summary of posts for a specific date.
    
    Args:
        date: Date in YYYY-MM-DD format (default: today)
    
    Returns:
        Dict with post counts and metrics by platform
    """
    if not date:
        date = datetime.now().strftime('%Y-%m-%d')
    
    try:
        if not SUMMARY_FILE.exists():
            return {}
        
        with open(SUMMARY_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse table rows
        lines = content.split('\n')
        posts = []
        
        for line in lines:
            if line.startswith('|') and date in line:
                parts = [p.strip() for p in line.split('|')[1:-1]]
                if len(parts) >= 5:
                    posts.append({
                        'timestamp': parts[0],
                        'platform': parts[1],
                        'post_id': parts[2],
                        'content': parts[3],
                        'metrics': parts[4]
                    })
        
        # Aggregate by platform
        summary = {}
        for post in posts:
            platform = post['platform']
            if platform not in summary:
                summary[platform] = {'count': 0, 'posts': []}
            summary[platform]['count'] += 1
            summary[platform]['posts'].append(post)
        
        return summary
        
    except Exception as e:
        print(f"Error getting daily summary: {e}")
        return {}


def get_weekly_summary() -> Dict:
    """
    Get summary of posts for the last 7 days.
    
    Returns:
        Dict with post counts and metrics by platform
    """
    from datetime import timedelta
    
    try:
        if not SUMMARY_FILE.exists():
            return {}
        
        with open(SUMMARY_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Calculate date range
        today = datetime.now()
        week_ago = today - timedelta(days=7)
        
        # Parse table rows
        lines = content.split('\n')
        posts = []
        
        for line in lines:
            if line.startswith('|'):
                parts = [p.strip() for p in line.split('|')[1:-1]]
                if len(parts) >= 5:
                    try:
                        post_date = datetime.strptime(parts[0][:10], '%Y-%m-%d')
                        if week_ago <= post_date <= today:
                            posts.append({
                                'timestamp': parts[0],
                                'platform': parts[1],
                                'post_id': parts[2],
                                'content': parts[3],
                                'metrics': parts[4]
                            })
                    except ValueError:
                        continue
        
        # Aggregate by platform
        summary = {
            'total_posts': len(posts),
            'by_platform': {},
            'posts': posts
        }
        
        for post in posts:
            platform = post['platform']
            if platform not in summary['by_platform']:
                summary['by_platform'][platform] = 0
            summary['by_platform'][platform] += 1
        
        return summary
        
    except Exception as e:
        print(f"Error getting weekly summary: {e}")
        return {}


def generate_summary_report() -> str:
    """
    Generate a formatted summary report for CEO briefing.
    
    Returns:
        Markdown formatted summary
    """
    try:
        weekly = get_weekly_summary()
        
        if not weekly or weekly['total_posts'] == 0:
            return "No social media posts in the last 7 days."
        
        report = f"""## Social Media Activity (Last 7 Days)

**Total Posts:** {weekly['total_posts']}

**By Platform:**
"""
        
        for platform, count in weekly['by_platform'].items():
            report += f"- {platform}: {count} posts\n"
        
        report += "\n**Recent Posts:**\n\n"
        
        # Show last 5 posts
        recent_posts = weekly['posts'][-5:]
        for post in reversed(recent_posts):
            report += f"- **{post['platform']}** ({post['timestamp']}): {post['content']}\n"
        
        return report
        
    except Exception as e:
        return f"Error generating summary report: {e}"


# Test function
def main():
    """Test the summary generator."""
    print("Testing Social Media Summary Generator...")
    
    # Test adding a post
    success = add_post_summary(
        platform="FACEBOOK",
        post_id="123456789",
        content_preview="This is a test post to verify the summary generation works correctly!",
        metrics={"likes": 50, "shares": 10, "comments": 5}
    )
    
    if success:
        print("✅ Post summary added successfully")
    else:
        print("❌ Failed to add post summary")
    
    # Test daily summary
    daily = get_daily_summary()
    print(f"\n📊 Daily Summary: {len(daily)} platforms")
    for platform, data in daily.items():
        print(f"  - {platform}: {data['count']} posts")
    
    # Test weekly summary
    weekly = get_weekly_summary()
    print(f"\n📊 Weekly Summary: {weekly.get('total_posts', 0)} total posts")
    
    # Test report generation
    report = generate_summary_report()
    print(f"\n📄 Summary Report:\n{report}")


if __name__ == "__main__":
    main()

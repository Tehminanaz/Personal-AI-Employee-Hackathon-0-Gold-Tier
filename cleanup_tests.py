#!/usr/bin/env python3
"""
Test Cleanup Script
Removes auto-generated and unnecessary test files, keeping only essential tests.
"""

import os
from pathlib import Path
import shutil

# Base directory
TESTS_DIR = Path(__file__).parent / "Tests"

# Essential tests to KEEP
ESSENTIAL_TESTS = [
    # Gold Tier integration tests (CRITICAL for hackathon)
    "test_gold_tier_integration.py",
    "test_gold_tier_final.py",
    
    # Core component tests
    "test_action_executor.py",
    "test_gmail_watcher.py",
    "test_provider_routing.py",
    
    # Template and examples
    "test_template_example.py",
    
    # Test data files (markdown)
    "FACEBOOK_POST_test.md",
    "INSTAGRAM_POST_test.md",
    "TWITTER_POST_test.md",
    "WHATSAPP_SEND_test.md",
    "ralph_test_task1.md",
    "ralph_test_task2.md",
    "TASK_COMPLETE.md",
    "README.md",
]

# Patterns to DELETE (auto-generated files)
DELETE_PATTERNS = [
    "test_P0_*",  # Auto-generated P0 tests
    "test_P1_*",  # Auto-generated P1 tests
    "test_GMAIL_SEND_*",  # Auto-generated Gmail tests
    "test_Gold_Tier_Final_Graduation_*",  # Duplicate graduation tests
    "test_ralph_analysis_*",  # Old Ralph tests
    "test_temp_*",  # Temporary tests
]

def should_keep(filename: str) -> bool:
    """Check if file should be kept"""
    # Keep essential files
    if filename in ESSENTIAL_TESTS:
        return True
    
    # Keep __pycache__ directory
    if filename == "__pycache__":
        return True
    
    # Delete files matching patterns
    for pattern in DELETE_PATTERNS:
        if Path(filename).match(pattern):
            return False
    
    # Delete other auto-generated tests not in essential list
    if filename.startswith("test_") and filename.endswith(".py"):
        if filename not in ESSENTIAL_TESTS:
            return False
    
    return True

def cleanup_tests():
    """Clean up test directory"""
    if not TESTS_DIR.exists():
        print(f"❌ Tests directory not found: {TESTS_DIR}")
        return
    
    print("=" * 60)
    print("Test Cleanup Script")
    print("=" * 60)
    print()
    
    files_to_delete = []
    files_to_keep = []
    
    # Scan directory
    for item in TESTS_DIR.iterdir():
        if should_keep(item.name):
            files_to_keep.append(item.name)
        else:
            files_to_delete.append(item)
    
    print(f"📊 Analysis:")
    print(f"  Total files: {len(list(TESTS_DIR.iterdir()))}")
    print(f"  Files to keep: {len(files_to_keep)}")
    print(f"  Files to delete: {len(files_to_delete)}")
    print()
    
    # Show what will be kept
    print("✅ Essential tests to KEEP:")
    for file in sorted(files_to_keep):
        print(f"  - {file}")
    print()
    
    # Confirm deletion
    print(f"⚠️  About to delete {len(files_to_delete)} files")
    print()
    
    response = input("Proceed with deletion? (yes/no): ").strip().lower()
    
    if response != "yes":
        print("❌ Cleanup cancelled")
        return
    
    # Delete files
    deleted_count = 0
    for file_path in files_to_delete:
        try:
            if file_path.is_file():
                file_path.unlink()
                deleted_count += 1
                print(f"  🗑️  Deleted: {file_path.name}")
        except Exception as e:
            print(f"  ❌ Error deleting {file_path.name}: {e}")
    
    print()
    print("=" * 60)
    print(f"✅ Cleanup complete! Deleted {deleted_count} files")
    print(f"📁 Remaining files: {len(list(TESTS_DIR.iterdir()))}")
    print("=" * 60)

if __name__ == "__main__":
    cleanup_tests()

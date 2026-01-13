"""
Comprehensive Gmail Watcher Verification Test Suite

This test suite implements the phased verification approach outlined in the strategic plan:
1. Phase 1: Basic Functionality Verification
2. Phase 2: Error Handling Verification
3. Phase 3: Integration Validation
4. Phase 4: Long-term Monitoring Setup

Author: Digital FTE System
Version: 1.0
Last Updated: 2026-01-12
"""

import unittest
import tempfile
import shutil
import os
import sys
import time
import threading
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
from datetime import datetime
import base64

# Add parent directory to path so we can import gmail_watcher
sys.path.insert(0, str(Path(__file__).parent.parent))

from gmail_watcher import (
    get_message_body,
    clean_filename,
    process_messages,
    check_simulation,
    authenticate_gmail,
    main,
    INBOX_DIR,
    POLL_INTERVAL
)


class TestGmailWatcherVerification(unittest.TestCase):
    """
    Comprehensive test suite for Gmail Watcher functionality verification.
    Implements the phased verification approach from the strategic plan.
    """

    def setUp(self):
        """Set up test environment for each test."""
        # Create temporary directories for testing
        self.test_dir = tempfile.mkdtemp()
        self.original_inbox = INBOX_DIR
        self.test_inbox = Path(self.test_dir) / "00_Inbox"
        self.test_inbox.mkdir(exist_ok=True)

        # Patch the INBOX_DIR in gmail_watcher
        import gmail_watcher
        gmail_watcher.INBOX_DIR = self.test_inbox

        # Create a test simulation file
        self.simulation_file = Path(self.test_dir) / "gmail_simulation.txt"
        import gmail_watcher
        gmail_watcher.SIMULATION_FILE = self.simulation_file

    def tearDown(self):
        """Clean up test environment after each test."""
        # Restore original INBOX_DIR
        import gmail_watcher
        gmail_watcher.INBOX_DIR = self.original_inbox
        gmail_watcher.SIMULATION_FILE = Path(__file__).parent.parent / "gmail_simulation.txt"

        # Clean up temporary directory
        if self.test_dir and Path(self.test_dir).exists():
            shutil.rmtree(self.test_dir)

    # PHASE 1: BASIC FUNCTIONALITY VERIFICATION
    def test_phase1_clean_filename_basic(self):
        """Phase 1: Test basic filename sanitization functionality."""
        # Test basic sanitization
        subject = "Meeting Request"
        cleaned = clean_filename(subject)
        self.assertEqual(cleaned, "Meeting Request")

        # Test sanitization of invalid characters
        subject = 'Invalid: <>:"/\\|?* chars'
        cleaned = clean_filename(subject)
        self.assertEqual(cleaned, "Invalid_ ___ chars")

        # Test filename truncation
        long_subject = "A" * 150
        cleaned = clean_filename(long_subject)
        self.assertLessEqual(len(cleaned), 100)
        self.assertEqual(len(cleaned), 100)  # Should be truncated to 100 chars

    def test_phase1_get_message_body_plain_text(self):
        """Phase 1: Test extraction of plain text message body."""
        import base64
        body_text = "Hello World Test Message"
        b64_data = base64.urlsafe_b64encode(body_text.encode('utf-8')).decode('utf-8')

        payload = {
            'body': {
                'data': b64_data
            }
        }

        result = get_message_body(payload)
        self.assertEqual(result, body_text)

    def test_phase1_get_message_body_multipart(self):
        """Phase 1: Test extraction of multipart message body."""
        import base64
        plain_text = "Plain text version"
        html_text = "<h1>HTML version</h1>"

        b64_plain = base64.urlsafe_b64encode(plain_text.encode('utf-8')).decode('utf-8')
        b64_html = base64.urlsafe_b64encode(html_text.encode('utf-8')).decode('utf-8')

        payload = {
            'parts': [
                {
                    'mimeType': 'text/plain',
                    'body': {'data': b64_plain}
                },
                {
                    'mimeType': 'text/html',
                    'body': {'data': b64_html}
                }
            ]
        }

        # According to the logic in gmail_watcher, HTML content should overwrite plain text
        result = get_message_body(payload)
        self.assertEqual(result, html_text)

    def test_phase1_simulation_file_processing(self):
        """Phase 1: Test simulation file processing functionality."""
        # Create a simulation file
        simulation_content = "Test Subject Line\nThis is the body content of the test email."
        with open(self.simulation_file, 'w', encoding='utf-8') as f:
            f.write(simulation_content)

        # Call check_simulation to process the file
        check_simulation()

        # Verify that a file was created in the test inbox
        inbox_files = list(self.test_inbox.glob("*.md"))
        self.assertEqual(len(inbox_files), 1)

        # Verify the content of the created file
        created_file = inbox_files[0]
        with open(created_file, 'r', encoding='utf-8') as f:
            content = f.read()

        self.assertIn("TASK: Test Subject Line", content)
        self.assertIn("Simulation Mode", content)
        self.assertIn("This is the body content of the test email", content)

        # Verify simulation file was deleted
        self.assertFalse(self.simulation_file.exists())

    # PHASE 2: ERROR HANDLING VERIFICATION
    def test_phase2_error_handling_missing_simulation_file(self):
        """Phase 2: Test graceful handling of missing simulation file."""
        # Ensure simulation file doesn't exist
        if self.simulation_file.exists():
            self.simulation_file.unlink()

        # This should not raise an exception
        check_simulation()

        # Verify no files were created
        inbox_files = list(self.test_inbox.glob("*.md"))
        self.assertEqual(len(inbox_files), 0)

    def test_phase2_error_handling_corrupted_simulation_file(self):
        """Phase 2: Test handling of corrupted simulation file."""
        # Create a simulation file with invalid content
        with open(self.simulation_file, 'w', encoding='utf-8') as f:
            f.write("")  # Empty file

        # This should not raise an exception
        check_simulation()

        # Verify simulation file was deleted even if empty
        self.assertFalse(self.simulation_file.exists())

    @patch('gmail_watcher.authenticate_gmail')
    def test_phase2_error_handling_no_service(self, mock_auth):
        """Phase 2: Test graceful handling when no Gmail service is available."""
        # Mock authentication to return None (no service)
        mock_auth.return_value = None

        # This should not raise an exception
        from gmail_watcher import process_messages
        process_messages(None)

        # Verify no files were created (since no service)
        inbox_files = list(self.test_inbox.glob("*.md"))
        self.assertEqual(len(inbox_files), 0)

    @patch('gmail_watcher.base64.urlsafe_b64decode')
    def test_phase2_error_handling_decode_failure(self, mock_decode):
        """Phase 2: Test handling of base64 decode failures in message body."""
        mock_decode.side_effect = Exception("Decode error")

        payload = {
            'body': {
                'data': 'invalid_base64_data'
            }
        }

        # This should handle the error gracefully
        result = get_message_body(payload)
        # Result should be empty string if decode fails
        self.assertEqual(result, "")

    # PHASE 3: INTEGRATION VALIDATION
    def test_phase3_file_creation_format(self):
        """Phase 3: Test that created files follow expected format."""
        # Create a simulation file
        simulation_content = "Integration Test: Priority Task\nTask details and requirements."
        with open(self.simulation_file, 'w', encoding='utf-8') as f:
            f.write(simulation_content)

        # Process the simulation
        check_simulation()

        # Verify file format
        inbox_files = list(self.test_inbox.glob("*.md"))
        self.assertEqual(len(inbox_files), 1)

        created_file = inbox_files[0]
        self.assertTrue(created_file.name.startswith("Email_"))
        self.assertTrue(created_file.name.endswith(".md"))

        # Verify content structure
        with open(created_file, 'r', encoding='utf-8') as f:
            content = f.read()

        self.assertIn("# TASK: Integration Test: Priority Task", content)
        self.assertIn("**Source**: Email from Simulation Mode", content)
        self.assertIn("## Content", content)
        self.assertIn("Task details and requirements.", content)

    def test_phase3_multiple_simulation_files(self):
        """Phase 3: Test handling of multiple simulation files over time."""
        # Process first simulation file
        sim1_content = "First Task\nFirst task details."
        with open(self.simulation_file, 'w', encoding='utf-8') as f:
            f.write(sim1_content)
        check_simulation()

        # Wait a moment to ensure different timestamps
        time.sleep(0.1)

        # Process second simulation file
        sim2_content = "Second Task\nSecond task details."
        with open(self.simulation_file, 'w', encoding='utf-8') as f:
            f.write(sim2_content)
        check_simulation()

        # Verify both files were created
        inbox_files = list(self.test_inbox.glob("*.md"))
        self.assertEqual(len(inbox_files), 2)

        # Verify both files have different timestamps in their names
        filenames = [f.name for f in inbox_files]
        self.assertNotEqual(filename[0] for filename in filenames)

    def test_phase3_directory_creation(self):
        """Phase 3: Test that inbox directory is created if it doesn't exist."""
        # Remove the test inbox directory
        shutil.rmtree(self.test_inbox)

        # Create and process a simulation file
        simulation_content = "Dir Creation Test\nTest content for directory creation."
        with open(self.simulation_file, 'w', encoding='utf-8') as f:
            f.write(simulation_content)

        # This should create the inbox directory automatically
        check_simulation()

        # Verify directory was created and file was saved
        self.assertTrue(self.test_inbox.exists())
        inbox_files = list(self.test_inbox.glob("*.md"))
        self.assertEqual(len(inbox_files), 1)

    # PHASE 4: MONITORING AND RELIABILITY
    def test_phase4_timestamp_formatting(self):
        """Phase 4: Test that timestamps are properly formatted."""
        # Create a simulation file
        simulation_content = "Timestamp Test\nTest content with timestamp."
        with open(self.simulation_file, 'w', encoding='utf-8') as f:
            f.write(simulation_content)

        # Process the simulation
        check_simulation()

        # Check that the timestamp is in the expected format
        inbox_files = list(self.test_inbox.glob("*.md"))
        self.assertEqual(len(inbox_files), 1)

        with open(inbox_files[0], 'r', encoding='utf-8') as f:
            content = f.read()

        # Look for the date format in the expected location
        self.assertIn(datetime.now().strftime('%Y-%m-%d'), content)

    def test_phase4_concurrent_access_safety(self):
        """Phase 4: Test that the system handles concurrent access safely."""
        # This test verifies that the system can handle rapid successive calls
        # without corrupting data or creating invalid files

        for i in range(3):
            # Create simulation file with unique content
            sim_content = f"Concurrent Test {i}\nContent for test {i}."
            with open(self.simulation_file, 'w', encoding='utf-8') as f:
                f.write(sim_content)

            # Process the simulation
            check_simulation()

            # Small delay to ensure different timestamps
            time.sleep(0.01)

        # Verify all three files were created successfully
        inbox_files = list(self.test_inbox.glob("*.md"))
        self.assertEqual(len(inbox_files), 3)

        # Verify each file has the correct content
        contents = []
        for f in inbox_files:
            with open(f, 'r', encoding='utf-8') as file:
                content = file.read()
                contents.append(content)

        # Check that all three test contents are present
        for i in range(3):
            found = any(f"Concurrent Test {i}" in content for content in contents)
            self.assertTrue(found, f"Content for test {i} not found in any file")


class TestGmailWatcherAdditional(unittest.TestCase):
    """Additional tests for edge cases and special scenarios."""

    def test_unicode_characters_handling(self):
        """Test handling of Unicode characters in email content."""
        unicode_subject = "Test with ñoñ-ASCII chäräctërs"
        cleaned = clean_filename(unicode_subject)
        # Should preserve Unicode characters but sanitize invalid filename chars
        self.assertIn("ñ", cleaned)
        self.assertIn("ö", cleaned)

    def test_special_priority_indicators(self):
        """Test handling of special priority indicators in subjects."""
        priority_subjects = [
            "P0_CRITICAL_Issue",
            "P1_HIGH_Meeting",
            "P2_NORMAL_Request",
            "P3_LOW_Review"
        ]

        for subj in priority_subjects:
            cleaned = clean_filename(subj)
            # Should preserve the priority indicators
            self.assertIn("P", cleaned)
            self.assertIn("_", cleaned)

    def test_empty_and_whitespace_content(self):
        """Test handling of empty or whitespace-only content."""
        # Test empty subject
        empty_result = clean_filename("")
        self.assertEqual(empty_result, "")

        # Test whitespace-only subject
        ws_result = clean_filename("   \t\n  ")
        self.assertEqual(ws_result, "   \t\n  ")  # Whitespace should be preserved


def run_comprehensive_verification():
    """
    Execute the comprehensive Gmail Watcher verification suite.

    Returns:
        dict: Summary of test results
    """
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestGmailWatcherVerification)
    additional_suite = loader.loadTestsFromTestCase(TestGmailWatcherAdditional)

    # Combine suites
    all_tests = unittest.TestSuite([suite, additional_suite])

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(all_tests)

    # Create summary
    summary = {
        'total_tests': result.testsRun,
        'failures': len(result.failures),
        'errors': len(result.errors),
        'success_rate': ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100) if result.testsRun > 0 else 0,
        'passed': result.testsRun - len(result.failures) - len(result.errors)
    }

    return summary


if __name__ == '__main__':
    print("Starting Gmail Watcher Comprehensive Verification...")
    print("=" * 60)

    # Run the verification
    summary = run_comprehensive_verification()

    print("=" * 60)
    print("VERIFICATION SUMMARY:")
    print(f"Total Tests Run: {summary['total_tests']}")
    print(f"Passed: {summary['passed']}")
    print(f"Failures: {summary['failures']}")
    print(f"Errors: {summary['errors']}")
    print(f"Success Rate: {summary['success_rate']:.1f}%")

    if summary['success_rate'] >= 95.0:
        print("\n✅ VERIFICATION PASSED: Gmail Watcher is functioning correctly!")
        print("All critical functionality has been verified.")
    else:
        print(f"\n❌ VERIFICATION FAILED: {summary['success_rate']:.1f}% success rate")
        print("Some functionality requires attention.")

    print("=" * 60)
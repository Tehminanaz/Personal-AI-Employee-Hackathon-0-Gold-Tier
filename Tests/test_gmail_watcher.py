import unittest
from unittest.mock import MagicMock, patch
import os
import sys
import shutil
from pathlib import Path

# Add parent directory to path so we can import gmail_watcher
sys.path.append(str(Path(__file__).parent.parent))

from gmail_watcher import get_message_body, clean_filename, INBOX_DIR

class TestGmailWatcher(unittest.TestCase):

    def setUp(self):
        # Create a temporary inbox for testing
        self.test_inbox = Path("tests/test_inbox")
        self.test_inbox.mkdir(exist_ok=True)
        # Patch the INBOX_DIR in gmail_watcher (though we aren't calling main, 
        # but just in case we were to test file writing directly via function)
        
    def tearDown(self):
        # Cleanup
        if self.test_inbox.exists():
            shutil.rmtree(self.test_inbox)

    def test_clean_filename(self):
        subject = "Important: Meeting / Review?"
        cleaned = clean_filename(subject)
        self.assertEqual(cleaned, "Important_ Meeting _ Review_")
        
        long_subject = "A" * 150
        cleaned_long = clean_filename(long_subject)
        self.assertEqual(len(cleaned_long), 100)

    def test_get_message_body_plain(self):
        # Mock plain text payload
        import base64
        body_text = "Hello World"
        b64_data = base64.urlsafe_b64encode(body_text.encode('utf-8')).decode('utf-8')
        
        payload = {
            'body': {
                'data': b64_data
            }
        }
        
        result = get_message_body(payload)
        self.assertEqual(result, body_text)

    def test_get_message_body_multipart(self):
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
        
        # Expect HTML version to be prioritized/returned as it overwrites plain in the loop
        # The logic in gmail_watcher:
        # plain -> body += ...
        # html -> body = ... (overwrite)
        # So we expect HTML content
        result = get_message_body(payload)
        self.assertEqual(result, html_text)

if __name__ == '__main__':
    unittest.main()

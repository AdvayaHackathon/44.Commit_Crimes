import os
import sys
import unittest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock

# Add app to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.ocr.processor import process_file, mock_ocr_process

class TestOCR(unittest.TestCase):
    """
    Test OCR processing functionality
    """

    def setUp(self):
        """
        Set up test environment
        """
        # Create test directories
        os.makedirs('data/input', exist_ok=True)
        os.makedirs('data/processed', exist_ok=True)
        os.makedirs('data/output', exist_ok=True)

        # Create a test PDF file
        with open('data/input/test.pdf', 'w') as f:
            f.write('Test PDF content')

        # Create a test image file
        with open('data/input/test.jpg', 'w') as f:
            f.write('Test image content')

    def tearDown(self):
        """
        Clean up test environment
        """
        # Remove test files
        if os.path.exists('data/input/test.pdf'):
            os.remove('data/input/test.pdf')

        if os.path.exists('data/input/test.jpg'):
            os.remove('data/input/test.jpg')

        # Remove processed files
        for file in os.listdir('data/processed'):
            if file.startswith('test_'):
                os.remove(os.path.join('data/processed', file))

    def test_mock_ocr_process_pdf(self):
        """
        Test mock OCR processing for PDF
        """
        # Run the test
        result = asyncio.run(mock_ocr_process('data/input/test.pdf', 'pdf'))

        # Check the result
        self.assertEqual(result['file_path'], 'data/input/test.pdf')
        self.assertEqual(result['file_type'], 'pdf')
        self.assertEqual(result['language'], 'en')
        self.assertIsNotNone(result['full_text'])
        self.assertIsNotNone(result['text_blocks'])
        self.assertEqual(result['page_count'], 3)

    def test_mock_ocr_process_image(self):
        """
        Test mock OCR processing for image
        """
        # Run the test
        result = asyncio.run(mock_ocr_process('data/input/test.jpg', 'image'))

        # Check the result
        self.assertEqual(result['file_path'], 'data/input/test.jpg')
        self.assertEqual(result['file_type'], 'image')
        self.assertEqual(result['language'], 'en')
        self.assertIsNotNone(result['full_text'])
        self.assertIsNotNone(result['text_blocks'])
        self.assertEqual(result['page_count'], 1)

    @patch('app.core.ocr.processor.process_with_google_vision', new_callable=AsyncMock)
    @patch('os.getenv')
    def test_process_file_with_credentials(self, mock_getenv, mock_process_with_google_vision):
        """
        Test process_file with Google credentials
        """
        # Mock environment variables
        mock_getenv.return_value = 'path/to/credentials.json'

        # Mock Google Vision processing
        mock_result = {
            'file_path': 'data/input/test.pdf',
            'file_type': 'pdf',
            'full_text': 'Test content',
            'text_blocks': [],
            'language': 'en',
            'page_count': 1
        }
        mock_process_with_google_vision.return_value = mock_result

        # Run the test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(process_file('data/input/test.pdf'))
        loop.close()

        # Check the result
        self.assertEqual(result, mock_result)
        mock_process_with_google_vision.assert_called_once_with('data/input/test.pdf', 'pdf')

    @patch('app.core.ocr.processor.mock_ocr_process', new_callable=AsyncMock)
    @patch('os.getenv')
    def test_process_file_without_credentials(self, mock_getenv, mock_mock_ocr_process):
        """
        Test process_file without Google credentials
        """
        # Mock environment variables
        mock_getenv.return_value = None

        # Mock mock OCR processing
        mock_result = {
            'file_path': 'data/input/test.pdf',
            'file_type': 'pdf',
            'full_text': 'Test content',
            'text_blocks': [],
            'language': 'en',
            'page_count': 1
        }
        mock_mock_ocr_process.return_value = mock_result

        # Run the test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(process_file('data/input/test.pdf'))
        loop.close()

        # Check the result
        self.assertEqual(result, mock_result)
        mock_mock_ocr_process.assert_called_once_with('data/input/test.pdf', 'pdf')

    def test_unsupported_file_type(self):
        """
        Test process_file with unsupported file type
        """
        # Create a test text file
        with open('data/input/test.txt', 'w') as f:
            f.write('Test text content')

        # Run the test
        with self.assertRaises(ValueError):
            asyncio.run(process_file('data/input/test.txt'))

        # Remove test file
        if os.path.exists('data/input/test.txt'):
            os.remove('data/input/test.txt')

if __name__ == '__main__':
    unittest.main()

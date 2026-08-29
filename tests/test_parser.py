"""
Unit tests for Resume Parser module.
"""

import unittest
from src.resume_parser import ResumeParser


class TestResumeParser(unittest.TestCase):

    def test_extract_text_from_txt(self):
        sample_txt = "John Doe\nEmail: john@example.com\nPhone: (555) 123-4567\nExperience: 5+ years of experience in Python"
        parsed = ResumeParser.parse_file(sample_txt, "john_doe.txt")

        self.assertEqual(parsed["candidate_name"], "John Doe")
        self.assertEqual(parsed["email"], "john@example.com")
        self.assertEqual(parsed["phone"], "(555) 123-4567")
        self.assertGreaterEqual(parsed["experience_years"], 5.0)

    def test_empty_resume_handling(self):
        with self.assertRaises(ValueError):
            ResumeParser.parse_file("", "empty.txt")

    def test_section_extraction(self):
        sample_text = """
        JANE SMITH
        
        EXPERIENCE
        Senior Developer at Tech Corp (2020 - 2024)
        
        EDUCATION
        B.S. Computer Science
        
        SKILLS
        Python, PyTorch, Docker
        """
        parsed = ResumeParser.parse_file(sample_text, "jane_smith.txt")
        sections = parsed["sections"]

        self.assertIn("Senior Developer", sections["Experience"])
        self.assertIn("B.S. Computer Science", sections["Education"])
        self.assertIn("Python", sections["Skills"])


if __name__ == "__main__":
    unittest.main()

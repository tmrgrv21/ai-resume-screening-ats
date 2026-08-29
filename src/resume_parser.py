"""
Resume Parser Module
Extracts text and key metadata (Name, Email, Phone, Sections, Years of Exp)
from PDF, DOCX, and TXT resume files.
"""

import io
import re
from typing import Dict, Any, Union, Optional
import pypdf
import docx

from src.text_preprocessor import clean_text


class ResumeParser:
    """
    Parses resume files (PDF, DOCX, TXT) and extracts structured data.
    """

    @staticmethod
    def extract_text_from_pdf(file_input: Union[str, bytes, io.BytesIO]) -> str:
        """Extracts text content from a PDF file input."""
        try:
            if isinstance(file_input, (bytes, io.BytesIO)):
                stream = io.BytesIO(file_input) if isinstance(file_input, bytes) else file_input
                reader = pypdf.PdfReader(stream)
            else:
                reader = pypdf.PdfReader(file_input)

            extracted_pages = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    extracted_pages.append(text)

            return "\n".join(extracted_pages)
        except Exception as e:
            raise ValueError(f"Error parsing PDF file: {str(e)}")

    @staticmethod
    def extract_text_from_docx(file_input: Union[str, bytes, io.BytesIO]) -> str:
        """Extracts text content from a DOCX file input."""
        try:
            if isinstance(file_input, bytes):
                stream = io.BytesIO(file_input)
                doc = docx.Document(stream)
            elif isinstance(file_input, io.BytesIO):
                doc = docx.Document(file_input)
            else:
                doc = docx.Document(file_input)

            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            # Also extract text from tables if any
            for table in doc.tables:
                for row in table.rows:
                    row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
                    if row_text:
                        paragraphs.append(row_text)

            return "\n".join(paragraphs)
        except Exception as e:
            raise ValueError(f"Error parsing DOCX file: {str(e)}")

    @staticmethod
    def extract_text_from_txt(file_input: Union[str, bytes, io.BytesIO]) -> str:
        """Extracts text content from a TXT file input, string content, or BytesIO."""
        try:
            if isinstance(file_input, bytes):
                return file_input.decode('utf-8', errors='ignore')
            elif isinstance(file_input, io.BytesIO):
                return file_input.getvalue().decode('utf-8', errors='ignore')
            elif isinstance(file_input, str):
                import os
                # If it's a path that exists on disk, read it
                if len(file_input) < 300 and os.path.exists(file_input):
                    with open(file_input, 'r', encoding='utf-8', errors='ignore') as f:
                        return f.read()
                # Otherwise, treat as direct text content
                return file_input
            else:
                return str(file_input)
        except Exception as e:
            raise ValueError(f"Error parsing TXT file: {str(e)}")

    @classmethod
    def parse_file(cls, file_input: Union[str, bytes, io.BytesIO], filename: str) -> Dict[str, Any]:
        """
        Main entry point for parsing resume file based on extension.
        Returns a structured dictionary with candidate metadata and text content.
        """
        ext = filename.split('.')[-1].lower() if '.' in filename else ''
        raw_text = ""

        if ext == 'pdf':
            raw_text = cls.extract_text_from_pdf(file_input)
        elif ext in ['docx', 'doc']:
            raw_text = cls.extract_text_from_docx(file_input)
        elif ext == 'txt':
            raw_text = cls.extract_text_from_txt(file_input)
        else:
            raise ValueError(f"Unsupported file format: .{ext}")

        cleaned = clean_text(raw_text, keep_case=True)

        if not cleaned or len(cleaned.strip()) < 10:
            raise ValueError("Resume file is empty or text could not be extracted.")

        # Metadata extraction
        candidate_name = cls.extract_name(cleaned, filename)
        email = cls.extract_email(cleaned)
        phone = cls.extract_phone(cleaned)
        experience_years = cls.estimate_experience_years(cleaned)
        sections = cls.extract_sections(cleaned)

        return {
            "filename": filename,
            "candidate_name": candidate_name,
            "email": email,
            "phone": phone,
            "raw_text": raw_text,
            "cleaned_text": cleaned,
            "experience_years": experience_years,
            "sections": sections
        }

    @staticmethod
    def extract_email(text: str) -> str:
        """Extracts email address using regular expression."""
        pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
        matches = re.findall(pattern, text)
        return matches[0] if matches else "Not detected"

    @staticmethod
    def extract_phone(text: str) -> str:
        """Extracts phone number using regex patterns."""
        pattern = r'(\+?\d{1,3}[\s\-]?)?\(?\d{3}\)?[\s\.-]?\d{3}[\s\.-]?\d{4}'
        matches = re.findall(pattern, text)
        if matches:
            # Re-search full matching string
            full_match = re.search(pattern, text)
            if full_match:
                return full_match.group(0).strip()
        return "Not detected"

    @staticmethod
    def extract_name(text: str, filename: str) -> str:
        """
        Extracts candidate name from filename or first non-empty lines of text.
        """
        # Try inferring from clean filename first
        clean_file = filename.rsplit('.', 1)[0]
        clean_file = re.sub(r'[-_]', ' ', clean_file)
        clean_file = re.sub(r'\b(resume|cv|profile|bio|draft)\b', '', clean_file, flags=re.IGNORECASE).strip()

        if len(clean_file) >= 2 and not clean_file.isdigit():
            return clean_file.title()

        # Fallback: check first 3 lines of resume
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        for line in lines[:3]:
            # Basic heuristic: 2-3 words, no numbers/symbols/emails/urls
            if 2 <= len(line.split()) <= 4 and not re.search(r'[@\d:\/]', line):
                return line.title()

        return "Candidate (" + filename + ")"

    @staticmethod
    def estimate_experience_years(text: str) -> float:
        """
        Estimates total experience in years based on date ranges (e.g. 2018 - 2023, 2021-Present)
        and explicit text statements (e.g. '5+ years of experience').
        """
        # Pattern 1: Explicit statements like "5+ years of experience" or "7 years experience"
        exp_pattern = r'(\d{1,2})\+?\s*(?:-\s*\d{1,2}\s*)?years?\s*(?:of\s*)?experience'
        matches = re.findall(exp_pattern, text, flags=re.IGNORECASE)
        if matches:
            try:
                nums = [float(m) for m in matches]
                return max(nums)
            except ValueError:
                pass

        # Pattern 2: Year ranges (e.g., 2017 - 2022, 2019 to Present)
        year_range_pattern = r'\b(20\d{2}|19\d{2})\s*(?:-|to|–|\/)\s*(20\d{2}|19\d{2}|present|current)\b'
        range_matches = re.findall(year_range_pattern, text, flags=re.IGNORECASE)

        total_years = 0.0
        current_year = 2026

        for start, end in range_matches:
            try:
                start_yr = int(start)
                end_yr = current_year if end.lower() in ['present', 'current'] else int(end)
                if end_yr >= start_yr:
                    total_years += (end_yr - start_yr)
            except ValueError:
                continue

        return round(min(total_years, 35.0), 1) if total_years > 0 else 0.0

    @staticmethod
    def extract_sections(text: str) -> Dict[str, str]:
        """
        Splits resume into key section chunks: Experience, Education, Projects, Skills, Certifications.
        """
        sections = {
            "Experience": "",
            "Education": "",
            "Skills": "",
            "Projects": "",
            "Certifications": ""
        }

        header_pattern = r'\n\s*(EXPERIENCE|WORK EXPERIENCE|EMPLOYMENT|EDUCATION|ACADEMICS|SKILLS|TECHNICAL SKILLS|PROJECTS|CERTIFICATIONS|PUBLICATIONS)\s*\n'

        splits = re.split(header_pattern, '\n' + text, flags=re.IGNORECASE)

        if len(splits) > 1:
            for i in range(1, len(splits) - 1, 2):
                header = splits[i].upper()
                content = splits[i + 1].strip()

                if any(kw in header for kw in ['EXPERIENCE', 'WORK', 'EMPLOYMENT']):
                    sections["Experience"] += "\n" + content
                elif any(kw in header for kw in ['EDUCATION', 'ACADEMIC']):
                    sections["Education"] += "\n" + content
                elif 'SKILL' in header:
                    sections["Skills"] += "\n" + content
                elif 'PROJECT' in header:
                    sections["Projects"] += "\n" + content
                elif 'CERTIFICAT' in header:
                    sections["Certifications"] += "\n" + content
        else:
            # Fallback if clear headers aren't detected
            sections["Experience"] = text[:1000]

        return {k: v.strip() for k, v in sections.items()}

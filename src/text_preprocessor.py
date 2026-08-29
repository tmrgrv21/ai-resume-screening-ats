"""
Text Preprocessor Module
Handles raw text normalization, cleaning, and demographic info masking for AI fairness.
"""

import re
import unicodedata
from typing import Dict, Any

DEMOGRAPHIC_PATTERNS = [
    # Gender indicators
    (r'\b(male|female|gender\s*:\s*(male|female|other)|sex\s*:\s*(male|female))\b', '[GENDER MASKED]'),
    # Age & Date of Birth indicators
    (r'\b(date\s*of\s*birth|dob|birth\s*date)\s*:\s*\d{1,2}[-/\.]\d{1,2}[-/\.]\d{2,4}\b', '[DOB MASKED]'),
    (r'\b(age\s*:\s*\d{2})\b', '[AGE MASKED]'),
    # Marital status indicators
    (r'\b(marital\s*status\s*:\s*(single|married|divorced|widowed)|status\s*:\s*(single|married))\b', '[MARITAL MASKED]'),
    (r'\b(single|married|divorced)\b', '[STATUS MASKED]'),
    # Nationality/Religion cues when labeled explicitly
    (r'\b(religion\s*:\s*\w+|nationality\s*:\s*\w+)\b', '[DEMOGRAPHIC MASKED]')
]


def clean_text(text: str, keep_case: bool = False) -> str:
    """
    Cleans and normalizes text while preserving technical skill syntax (e.g. C++, .NET, Node.js).
    """
    if not text or not isinstance(text, str):
        return ""

    # Normalize unicode characters
    text = unicodedata.normalize('NFKD', text)

    # Convert tabs and carriage returns to space
    text = re.sub(r'[\r\t]+', ' ', text)

    # Replace multiple newlines with a single line break marker or space
    text = re.sub(r'\n+', '\n', text)

    # Remove unprintable / non-ascii control chars except common punctuation
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)

    # Collapse multiple whitespaces
    text = re.sub(r'[ \t]+', ' ', text)

    if not keep_case:
        text = text.strip()
    else:
        text = text.strip()

    return text


def mask_demographics(text: str) -> str:
    """
    Masks demographic details (gender, age, marital status, religion, nationality)
    to ensure fairness and un-biased candidate ranking.
    """
    if not text:
        return ""

    masked_text = text
    for pattern, replacement in DEMOGRAPHIC_PATTERNS:
        masked_text = re.sub(pattern, replacement, masked_text, flags=re.IGNORECASE)

    return masked_text


def preprocess_for_embedding(text: str) -> str:
    """
    Preprocesses text for SentenceTransformer embedding generation.
    Cleans text and masks demographic data.
    """
    cleaned = clean_text(text)
    masked = mask_demographics(cleaned)
    return masked


class TextPreprocessor:
    """
    Class wrapper for text preprocessing and demographic masking operations.
    """
    @staticmethod
    def clean_text(text: str, keep_case: bool = False) -> str:
        return clean_text(text, keep_case=keep_case)

    @staticmethod
    def mask_demographic_cues(text: str) -> Dict[str, Any]:
        masked = mask_demographics(text)
        return {"masked_text": masked}

    @staticmethod
    def preprocess_for_embedding(text: str) -> str:
        return preprocess_for_embedding(text)

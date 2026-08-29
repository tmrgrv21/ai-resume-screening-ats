"""
Semantic Matcher Module
Computes semantic embedding similarity between job description and resume text
using SentenceTransformers (sentence-transformers/all-MiniLM-L6-v2) with TF-IDF fallback.
"""

import numpy as np
from typing import List, Tuple, Union, Optional
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer

# Global model cache placeholder
_TRANSFORMER_MODEL = None


def get_sentence_transformer_model(model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
    """
    Lazy loader & singleton cache for SentenceTransformer model.
    """
    global _TRANSFORMER_MODEL
    if _TRANSFORMER_MODEL is None:
        try:
            from sentence_transformers import SentenceTransformer
            _TRANSFORMER_MODEL = SentenceTransformer(model_name)
        except Exception as e:
            print(f"Warning: Could not load SentenceTransformer ({e}). TF-IDF fallback will be used.")
            _TRANSFORMER_MODEL = False
    return _TRANSFORMER_MODEL


class SemanticMatcher:
    """
    Computes semantic similarity scores between Job Description and Resume text.
    """

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = get_sentence_transformer_model(model_name)

    def compute_similarity(self, job_text: str, resume_text: str) -> Tuple[float, str]:
        """
        Computes semantic similarity between job description and resume text.
        Returns:
            Tuple[float, str]: (Similarity Score 0.0-100.0, Method used: 'SentenceTransformer' or 'TF-IDF')
        """
        if not job_text or not resume_text:
            return 0.0, "Empty Input"

        # Try SentenceTransformer embedding matching first
        if self.model:
            try:
                embeddings = self.model.encode([job_text, resume_text], normalize_embeddings=True)
                sim = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]

                # Cosine similarity for normalized vectors ranges [-1, 1], map to [0, 100]
                scaled_score = float(max(0.0, sim)) * 100.0
                return round(scaled_score, 2), "SentenceTransformer (all-MiniLM-L6-v2)"
            except Exception as e:
                print(f"Embedding computation error: {e}. Falling back to TF-IDF.")

        # Fallback: TF-IDF Cosine Similarity
        return self._tfidf_similarity(job_text, resume_text), "TF-IDF N-Gram Similarity (Fallback)"

    @staticmethod
    def _tfidf_similarity(text1: str, text2: str) -> float:
        """
        TF-IDF vectorizer fallback with sublinear scaling and word+char n-grams.
        """
        try:
            vectorizer = TfidfVectorizer(
                stop_words='english',
                ngram_range=(1, 3),
                sublinear_tf=True,
                token_pattern=r'(?u)\b\w+\b'
            )
            tfidf_matrix = vectorizer.fit_transform([text1, text2])
            sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            return round(float(max(0.0, sim)) * 100.0, 2)
        except Exception:
            return 0.0

"""Utilities for extracting and normalizing resume text from PDF files."""

from __future__ import annotations

import io
import re
from pathlib import Path
from typing import BinaryIO, Union

import pdfplumber
from PyPDF2 import PdfReader

PDFSource = Union[str, Path, BinaryIO]


class ResumeReadError(Exception):
    """Raised when a resume PDF cannot be parsed into meaningful text."""


def _to_bytes_buffer(source: PDFSource) -> io.BytesIO:
    """Convert multiple input types to an in-memory bytes buffer."""
    if isinstance(source, (str, Path)):
        return io.BytesIO(Path(source).expanduser().read_bytes())

    if hasattr(source, "getvalue"):
        data = source.getvalue()
    elif hasattr(source, "read"):
        if hasattr(source, "seek"):
            source.seek(0)
        data = source.read()
    else:
        raise TypeError("Unsupported PDF input type.")

    if isinstance(data, str):
        data = data.encode("utf-8", errors="ignore")

    if not isinstance(data, (bytes, bytearray)):
        raise TypeError("PDF input must resolve to bytes.")

    return io.BytesIO(bytes(data))


def _extract_with_pdfplumber(buffer: io.BytesIO) -> str:
    """Extract text using pdfplumber for layout-friendly parsing."""
    buffer.seek(0)
    text_chunks: list[str] = []
    with pdfplumber.open(buffer) as pdf:
        for page in pdf.pages:
            text_chunks.append(page.extract_text() or "")
    return "\n".join(text_chunks)


def _extract_with_pypdf2(buffer: io.BytesIO) -> str:
    """Fallback extraction using PyPDF2."""
    buffer.seek(0)
    text_chunks: list[str] = []
    reader = PdfReader(buffer)
    for page in reader.pages:
        text_chunks.append(page.extract_text() or "")
    return "\n".join(text_chunks)


def normalize_text(text: str) -> str:
    """Clean text artifacts while preserving paragraph structure."""
    cleaned = text.replace("\x00", " ")
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r"[ \t]+\n", "\n", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def extract_text_from_pdf(source: PDFSource) -> str:
    """
    Extract text from a PDF source.

    Strategy:
    1) Try pdfplumber.
    2) Fallback to PyPDF2.
    3) Raise ResumeReadError if both fail or return empty output.
    """
    buffer = _to_bytes_buffer(source)
    extraction_errors: list[str] = []

    for extractor in (_extract_with_pdfplumber, _extract_with_pypdf2):
        try:
            raw_text = extractor(buffer)
            normalized = normalize_text(raw_text)
            if normalized:
                return normalized
        except Exception as exc:  # noqa: BLE001
            extraction_errors.append(f"{extractor.__name__}: {exc}")

    error_details = "; ".join(extraction_errors) if extraction_errors else "No text found in PDF."
    raise ResumeReadError(
        "Unable to extract text from the uploaded PDF resume. "
        f"Details: {error_details}"
    )


__all__ = ["ResumeReadError", "extract_text_from_pdf", "normalize_text"]

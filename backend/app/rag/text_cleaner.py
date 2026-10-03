import re
from typing import Optional


class TextCleaner:
    """
    Cleans and normalizes extracted automotive technical documentation.
    Preserves heading structures, diagnostic codes, and tabular specs.
    """

    @staticmethod
    def clean(text: str) -> str:
        if not text:
            return ""

        # Normalize line breaks
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        # Remove repetitive header/footer page artifacts like "Page 12 of 150" or standalone numbers
        text = re.sub(r"\n\s*(?:Page\s+\d+(?:\s+of\s+\d+)?|\d+)\s*\n", "\n", text, flags=re.IGNORECASE)

        # Replace non-breaking spaces and exotic whitespace
        text = re.sub(r"[\u00A0\u1680\u2000-\u200B\u202F\u205F\u3000]", " ", text)

        # Remove excessive repeated dashes or underscores (often used as divider lines in manuals)
        text = re.sub(r"[-_=]{4,}", "---", text)

        # Collapse excessive blank lines (more than 2 consecutive newlines)
        text = re.sub(r"\n{3,}", "\n\n", text)

        # Strip trailing/leading spaces on each line
        lines = [line.strip() for line in text.split("\n")]
        text = "\n".join(lines)

        return text.strip()

    @staticmethod
    def extract_section_title(text: str) -> Optional[str]:
        """
        Attempts to detect a section or heading from text start (e.g., '### SECTION 1: COOLING SYSTEM').
        """
        first_line = text.strip().split("\n")[0] if text else ""
        if first_line.startswith("#") or first_line.isupper() or ":" in first_line:
            clean_title = re.sub(r"^[#\s\-*]+", "", first_line).strip()
            if 3 < len(clean_title) < 120:
                return clean_title
        return None

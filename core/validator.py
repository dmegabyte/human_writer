import re
from typing import List, Optional

class SlopValidator:
    def __init__(
        self,
        stop_words: Optional[List[str]] = None,
        ban_dashes: bool = True,
        ban_names: bool = True
    ):
        self.stop_words = stop_words or [
            "для нас важно", "стоит отметить", "порадовало, что", "особенно приятно",
            "по факту", "честно говоря", "приятно, что", "соблюдены", "дают выбор",
            "поставлены плотно", "спокойные и адекватные", "в любой сезон",
            "круглый год", "спроектированы", "лотов", "данный объект"
        ]
        self.ban_dashes = ban_dashes
        self.ban_names = ban_names

    def validate_review(self, text: str, forbidden_names: Optional[List[str]] = None):
        clean_text = re.sub(r"^\[.*?\]\s*", "", text)
        low_text = clean_text.lower()

        if self.ban_dashes:
            if "—" in clean_text or "–" in clean_text:
                raise ValueError(f"SlopValidator: text contains banned dash: {clean_text}")

        for sw in self.stop_words:
            if sw in low_text:
                raise ValueError(f"SlopValidator: stop-word '{sw}' detected in: {clean_text}")

        if self.ban_names and forbidden_names:
            for name in forbidden_names:
                if len(name) >= 4 and re.search(rf"\b{re.escape(name.lower())}\b", low_text):
                    raise ValueError(f"SlopValidator: target name '{name}' leaked in: {clean_text}")

    def validate_batch(self, reviews: List[str], forbidden_names: Optional[List[str]] = None):
        for r in reviews:
            self.validate_review(r, forbidden_names)

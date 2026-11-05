import re
from typing import List, Optional, Dict, Any

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

        # Обычные русские слова, которые могут совпадать с названиями ЖК ("ЖК Соседи", "ЖК Время", "ЖК Отлично")
        self.common_russian_words = {
            "соседи", "время", "лучи", "высота", "свои", "утро", "весна", "парк",
            "река", "город", "квартал", "дом", "свет", "маяк", "небо", "волна",
            "отлично", "хорошо", "норма", "плюс", "старт", "комфорт", "союз"
        }

    def validate_review(
        self,
        text: str,
        forbidden_names: Optional[List[str]] = None,
        facts: Optional[Dict[str, Any]] = None
    ):
        clean_text = re.sub(r"^\[.*?\]\s*", "", text)
        low_text = clean_text.lower()

        # 1. Запрет тире
        if self.ban_dashes:
            if "—" in clean_text or "–" in clean_text:
                raise ValueError(f"SlopValidator: text contains banned dash: {clean_text}")

        # 2. Стоп-слова
        for sw in self.stop_words:
            if sw in low_text:
                raise ValueError(f"SlopValidator: stop-word '{sw}' detected in: {clean_text}")

        # 3. Запрет названий ЖК
        if self.ban_names and forbidden_names:
            for name in forbidden_names:
                name_clean = name.strip()
                if len(name_clean) >= 4 and name_clean.lower() not in self.common_russian_words:
                    if re.search(rf"\b{re.escape(name_clean.lower())}\b", low_text):
                        raise ValueError(f"SlopValidator: target name '{name}' leaked in: {clean_text}")

        # 4. СТРОГИЙ FACT-LOCKING (Защита от галлюцинаций)
        if facts is not None:
            if not facts.get("has_parking", False) and "паркинг" in low_text:
                raise ValueError(f"FactLocking Error: parking mentioned but building has no parking: {clean_text}")
            
            if not facts.get("has_stroller_room", False) and "колясочн" in low_text:
                raise ValueError(f"FactLocking Error: stroller room mentioned but not confirmed: {clean_text}")
            
            if not facts.get("has_closed_yard", False) and ("без машин" in low_text or "закрыт от машин" in low_text):
                raise ValueError(f"FactLocking Error: closed yard mentioned but not confirmed: {clean_text}")
            
            if not facts.get("has_concierge", False) and "консьерж" in low_text:
                raise ValueError(f"FactLocking Error: concierge mentioned but not confirmed: {clean_text}")
            
            if not facts.get("has_security", False) and "охрана на въезде" in low_text:
                raise ValueError(f"FactLocking Error: gate security mentioned but not confirmed: {clean_text}")

    def validate_batch(
        self,
        reviews: List[str],
        forbidden_names: Optional[List[str]] = None,
        facts: Optional[Dict[str, Any]] = None
    ):
        for r in reviews:
            self.validate_review(r, forbidden_names, facts)

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional
import json

@dataclass
class WriterConfig:
    project_name: str = "default_project"
    preset_name: str = "real_estate"
    
    # Режимы и тумблеры улучшений
    enable_hyperlocal: bool = True       # подмешивать реальные топонимы/факты (район, потолки, улицу)
    enable_personas: bool = True         # использовать ролевые маски (мама, технарь, автомобилист, удаленщик)
    enable_persona_tags: bool = True     # выводить в теге персону и тему: [Средний | Мама с коляской | Вход без порогов]
    enable_burstiness: bool = True       # живой рубленый ритм речи
    slang_level: str = "medium"          # "none", "medium", "high"
    
    # Правила качества (Slop-Shield)
    ban_dashes: bool = True
    ban_target_names: bool = True
    stop_words: List[str] = field(default_factory=lambda: [
        "для нас важно", "стоит отметить", "порадовало, что", "особенно приятно",
        "по факту", "честно говоря", "приятно, что", "соблюдены", "дают выбор",
        "поставлены плотно", "спокойные и адекватные", "в любой сезон",
        "круглый год", "спроектированы", "лотов", "данный объект"
    ])
    
    # Структура слотов на 1 карточку
    super_shorts_count: int = 7
    shorts_count: int = 2
    mediums_count: int = 2
    longs_count: int = 1

    def to_dict(self) -> dict:
        """Сериализация конфига в словарь для REST API / UI."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "WriterConfig":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    @classmethod
    def load_json(cls, filepath: str) -> "WriterConfig":
        with open(filepath, "r", encoding="utf-8") as f:
            return cls.from_dict(json.load(f))

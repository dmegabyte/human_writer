from typing import Dict, Any, List, Optional
from core.config import WriterConfig
from core.validator import SlopValidator

class HumanWriterEngine:
    def __init__(self, preset_module, config: Optional[WriterConfig] = None, validator: Optional[SlopValidator] = None):
        self.preset = preset_module
        self.config = config or WriterConfig()
        self.validator = validator or SlopValidator(
            stop_words=self.config.stop_words,
            ban_dashes=self.config.ban_dashes,
            ban_names=self.config.ban_target_names
        )

    def _format_tag(self, length_type: str, persona: Optional[str] = None, topic: Optional[str] = None) -> str:
        if not self.config.enable_persona_tags or not persona:
            return f"[{length_type}]"
        
        parts = [length_type, persona]
        if topic:
            parts.append(topic)
        return f"[{' | '.join(parts)}]"

    def generate_complex_reviews(self, idx: int, facts: Optional[Dict[str, Any]] = None) -> List[str]:
        facts = facts or {}
        has_parking = bool(facts.get("has_parking", False))
        district = str(facts.get("district", "")).strip()
        ceiling_height = facts.get("ceiling_height")

        p = self.preset
        cfg = self.config
        revs = []

        # 1. Суперкороткие (7 штук с уникальными стартерами и темами)
        super_short_categories = [
            ("Окна", p.CAT_0_WINDOWS),
            ("Отопление", p.CAT_1_HEATING),
            ("Вода", p.CAT_2_WATER),
            ("Лифты", p.CAT_3_ELEVATORS),
            ("Подъезд", p.CAT_4_ENTRANCE),
            ("Двор", p.CAT_5_COURTYARD),
            ("Безопасность", p.CAT_6_SECURITY)
        ]
        for cat_idx in range(cfg.super_shorts_count):
            topic_name, pool = super_short_categories[cat_idx % len(super_short_categories)]
            tag = self._format_tag("Суперкороткий", "Жилец", topic_name)
            revs.append(f"{tag} {pool[idx % len(pool)]}")

        # 2. Короткие
        tag_infra = self._format_tag("Короткий", "Пешеход", "Инфраструктура")
        revs.append(f"{tag_infra} {p.SHORT_0_INFRA[idx % len(p.SHORT_0_INFRA)]}")
        
        # Если включена гиперлокальность и известны потолки
        if cfg.enable_hyperlocal and ceiling_height and float(ceiling_height) >= 3.0:
            tag_quality = self._format_tag("Короткий", "Новосел", "Высокие потолки")
            revs.append(f"{tag_quality} Потолки {ceiling_height} метра дают колоссальное ощущение простора и света в комнатах.")
        else:
            tag_quality = self._format_tag("Короткий", "Новосел", "Качество дома")
            revs.append(f"{tag_quality} {p.SHORT_1_QUALITY[idx % len(p.SHORT_1_QUALITY)]}")

        # 3. Средние (Ролевые маски)
        if cfg.enable_personas:
            # Чередуем роли по остатку от деления индекса
            if idx % 2 == 0:
                # Мама + Технарь
                tag_p1 = self._format_tag("Средний", "Мама с коляской", "Вход без порогов и площадка")
                revs.append(f"{tag_p1} {p.MED_PERSONA_FAMILY[idx % len(p.MED_PERSONA_FAMILY)]}")

                tag_p2 = self._format_tag("Средний", "Мастер ремонта", "Стяжка и геометрия стен")
                revs.append(f"{tag_p2} {p.MED_PERSONA_TECH[idx % len(p.MED_PERSONA_TECH)]}")
            else:
                # Удаленка + Автомобилист (или Мама если нет паркинга)
                tag_p1 = self._format_tag("Средний", "Удаленщик", "Тишина и интернет")
                revs.append(f"{tag_p1} {p.MED_PERSONA_REMOTE[idx % len(p.MED_PERSONA_REMOTE)]}")

                if has_parking:
                    tag_p2 = self._format_tag("Средний", "Автомобилист", "Подземный паркинг и выезд")
                    revs.append(f"{tag_p2} {p.MED_PERSONA_AUTO[idx % len(p.MED_PERSONA_AUTO)]}")
                else:
                    tag_p2 = self._format_tag("Средний", "Мама с коляской", "Безопасный двор")
                    revs.append(f"{tag_p2} {p.MED_PERSONA_FAMILY[idx % len(p.MED_PERSONA_FAMILY)]}")
        else:
            tag_m1 = self._format_tag("Средний", "Жилец", "Отделка")
            tag_m2 = self._format_tag("Средний", "Жилец", "УК и сервис")
            revs.append(f"{tag_m1} {p.MED_0_FLAT_NEUTRAL[idx % len(p.MED_0_FLAT_NEUTRAL)]}")
            revs.append(f"{tag_m2} {p.MED_1_MGMT_NEUTRAL[idx % len(p.MED_1_MGMT_NEUTRAL)]}")

        # 4. Длинный нарратив
        tag_long = self._format_tag("Развернутый", "Семья с ребенком", "Опыт проживания")
        if cfg.enable_hyperlocal and district and len(district) >= 3 and district.lower() not in ["msk", "spb"]:
            l1 = f"Квартиру искали именно в районе {district}, чтобы жить в привычном окружении и не тратить часы на поездки."
        else:
            l1 = p.LONG_S1_BASE[idx % len(p.LONG_S1_BASE)]

        long_s2_pool = p.LONG_S2_BASE + (["Лифты спускаются прямо на уровень паркинга, что колоссально экономит время в холодные месяцы."] if has_parking else [])
        l2 = long_s2_pool[(idx // len(p.LONG_S1_BASE)) % len(long_s2_pool)]
        l3 = p.LONG_S3_BASE[(idx // (len(p.LONG_S1_BASE) * len(long_s2_pool))) % len(p.LONG_S3_BASE)]
        revs.append(f"{tag_long} {l1} {l2} {l3}")

        # Quality Gate validation
        target_names = facts.get("target_names", [])
        self.validator.validate_batch(revs, forbidden_names=target_names)

        return revs

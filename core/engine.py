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
        has_closed_yard = bool(facts.get("has_closed_yard", False))
        has_stroller_room = bool(facts.get("has_stroller_room", False))
        has_concierge = bool(facts.get("has_concierge", False))
        has_park_near = bool(facts.get("has_park_near", False))
        district = str(facts.get("district", "")).strip()
        ceiling_height = facts.get("ceiling_height")

        p = self.preset
        cfg = self.config
        revs = []

        # 1. Суперкороткие (7 штук с гарантированно уникальными стартерами)
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
        # Если есть парк рядом — используем факт парка!
        if cfg.enable_hyperlocal and has_park_near:
            tag_infra = self._format_tag("Короткий", "Пешеход", "Парк рядом")
            revs.append(f"{tag_infra} {p.SHORT_0_INFRA_PARK[idx % len(p.SHORT_0_INFRA_PARK)]}")
        else:
            tag_infra = self._format_tag("Короткий", "Пешеход", "Инфраструктура")
            revs.append(f"{tag_infra} {p.SHORT_0_INFRA_BASE[idx % len(p.SHORT_0_INFRA_BASE)]}")

        # Если потолки высокие — используем факт потолков!
        if cfg.enable_hyperlocal and ceiling_height and float(ceiling_height) >= 3.0:
            tag_quality = self._format_tag("Короткий", "Новосел", "Высокие потолки")
            revs.append(f"{tag_quality} Потолки {ceiling_height} метра дают колоссальное ощущение простора и света в комнатах.")
        else:
            tag_quality = self._format_tag("Короткий", "Новосел", "Качество дома")
            revs.append(f"{tag_quality} {p.SHORT_1_QUALITY[idx % len(p.SHORT_1_QUALITY)]}")

        # 3. Средние: ролевые маски с динамическим fact-locking
        if cfg.enable_personas:
            # Чередуем пары ролей по индексу дома
            if idx % 2 == 0:
                # Роль 1: Мама с коляской
                if has_stroller_room:
                    tag_p1 = self._format_tag("Средний", "Мама с коляской", "Колясочная и вход")
                    body_p1 = p.MED_FAMILY_STROLLER_ROOM[idx % len(p.MED_FAMILY_STROLLER_ROOM)]
                elif has_closed_yard:
                    tag_p1 = self._format_tag("Средний", "Мама с коляской", "Закрытый двор")
                    body_p1 = p.MED_FAMILY_CLOSED_YARD[idx % len(p.MED_FAMILY_CLOSED_YARD)]
                else:
                    tag_p1 = self._format_tag("Средний", "Мама с коляской", "Вход без порогов и площадка")
                    body_p1 = p.MED_FAMILY_BASE[idx % len(p.MED_FAMILY_BASE)]
                revs.append(f"{tag_p1} {body_p1}")

                # Роль 2: Мастер ремонта
                tag_p2 = self._format_tag("Средний", "Мастер ремонта", "Стяжка и геометрия стен")
                revs.append(f"{tag_p2} {p.MED_TECH_BASE[idx % len(p.MED_TECH_BASE)]}")
            else:
                # Роль 1: Удаленщик
                tag_p1 = self._format_tag("Средний", "Удаленщик", "Тишина и интернет")
                revs.append(f"{tag_p1} {p.MED_REMOTE_BASE[idx % len(p.MED_REMOTE_BASE)]}")

                # Роль 2: Автомобилист (если есть паркинг) / Консьерж (если есть) / Семья
                if has_parking:
                    tag_p2 = self._format_tag("Средний", "Автомобилист", "Подземный паркинг")
                    body_p2 = p.MED_AUTO_PARKING[idx % len(p.MED_AUTO_PARKING)]
                elif has_concierge:
                    tag_p2 = self._format_tag("Средний", "Жилец", "Консьерж-сервис")
                    body_p2 = p.MED_MGMT_CONCIERGE[idx % len(p.MED_MGMT_CONCIERGE)]
                else:
                    tag_p2 = self._format_tag("Средний", "Мама с коляской", "Тротуары и площадка")
                    body_p2 = p.MED_FAMILY_BASE[idx % len(p.MED_FAMILY_BASE)]
                revs.append(f"{tag_p2} {body_p2}")
        else:
            tag_m1 = self._format_tag("Средний", "Жилец", "Отделка")
            tag_m2 = self._format_tag("Средний", "Жилец", "УК и сервис")
            revs.append(f"{tag_m1} {p.MED_TECH_BASE[idx % len(p.MED_TECH_BASE)]}")
            revs.append(f"{tag_m2} {p.MED_FAMILY_BASE[idx % len(p.MED_FAMILY_BASE)]}")

        # 4. Длинный нарратив (3 предложения)
        tag_long = self._format_tag("Развернутый", "Семья с ребенком", "Опыт проживания")
        if cfg.enable_hyperlocal and district and len(district) >= 3 and district.lower() not in ["msk", "spb", "perm"]:
            l1 = f"Квартиру искали именно в районе {district}, чтобы жить в привычном окружении и не тратить часы на поездки."
        else:
            l1 = p.LONG_S1_BASE[idx % len(p.LONG_S1_BASE)]

        # Динамический пул второго предложения
        s2_pool = list(p.LONG_S2_BASE)
        if has_closed_yard:
            s2_pool.append(p.LONG_S2_CLOSED_YARD)
        if has_parking:
            s2_pool.append(p.LONG_S2_PARKING)

        l2 = s2_pool[(idx // len(p.LONG_S1_BASE)) % len(s2_pool)]
        l3 = p.LONG_S3_BASE[(idx // (len(p.LONG_S1_BASE) * len(s2_pool))) % len(p.LONG_S3_BASE)]
        revs.append(f"{tag_long} {l1} {l2} {l3}")

        # СТРОГАЯ ВАЛИДАЦИЯ С УЧЕТОМ ФАКТОВ
        target_names = facts.get("target_names", [])
        self.validator.validate_batch(revs, forbidden_names=target_names, facts=facts)

        return revs

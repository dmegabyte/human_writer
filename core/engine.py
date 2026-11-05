import re
import random
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

    def _resolve_spintax(self, text: str, rng: random.Random) -> str:
        """Раскрывает спин-синтаксис вида {вариант1|вариант2|вариант3}."""
        if not self.config.enable_spintax or "{" not in text:
            # Если спинтакс отключен, подставляем первый вариант
            return re.sub(r"\{([^{}|]+)(?:\|[^{}]+)*\}", r"\1", text)
        
        pattern = re.compile(r"\{([^{}]+)\}")
        while True:
            match = pattern.search(text)
            if not match:
                break
            options = match.group(1).split("|")
            chosen = rng.choice(options)
            text = text[:match.start()] + chosen + text[match.end():]
        return text

    def generate_complex_reviews(self, idx: int, facts: Optional[Dict[str, Any]] = None) -> List[str]:
        facts = facts or {}
        has_parking = bool(facts.get("has_parking", False))
        has_closed_yard = bool(facts.get("has_closed_yard", False))
        has_stroller_room = bool(facts.get("has_stroller_room", False))
        has_concierge = bool(facts.get("has_concierge", False))
        has_park_near = bool(facts.get("has_park_near", False))
        has_water_near = bool(facts.get("has_water_near", False))
        metro_station = facts.get("metro_station")
        highway_name = facts.get("highway_name")
        finish_type = facts.get("finish_type")
        district = str(facts.get("district", "")).strip()
        ceiling_height = facts.get("ceiling_height")

        p = self.preset
        cfg = self.config
        revs = []

        # 1. СУПЕРКОРОТКИЕ КАТЕГОРИИ (С ротацией тем, спин-синтаксисом и Vibe-контролем)
        tech_cats = [
            ("Окна", p.CAT_0_WINDOWS),
            ("Отопление", p.CAT_1_HEATING),
            ("Вода", p.CAT_2_WATER),
            ("Стены", getattr(p, "CAT_7_WALLS", p.CAT_0_WINDOWS)),
            ("Свет", getattr(p, "CAT_9_LIGHT", p.CAT_1_HEATING)),
            ("Балкон", getattr(p, "CAT_8_BALCONY", p.CAT_0_WINDOWS)),
            ("Лифты", p.CAT_3_ELEVATORS),
        ]
        warm_cats = [
            ("Двор", p.CAT_5_COURTYARD),
            ("Подъезд", p.CAT_4_ENTRANCE),
            ("Безопасность", p.CAT_6_SECURITY),
            ("Холл", getattr(p, "CAT_10_STORAGE", p.CAT_4_ENTRANCE)),
            ("Лифты", p.CAT_3_ELEVATORS),
            ("Окна", p.CAT_0_WINDOWS),
            ("Отопление", p.CAT_1_HEATING),
        ]

        if cfg.vibe == "pragmatic":
            pool_base = tech_cats + warm_cats[:4]
        elif cfg.vibe == "warm":
            pool_base = warm_cats + tech_cats[:4]
        else:
            # Balanced
            pool_base = [
                ("Окна", p.CAT_0_WINDOWS),
                ("Отопление", p.CAT_1_HEATING),
                ("Вода", p.CAT_2_WATER),
                ("Лифты", p.CAT_3_ELEVATORS),
                ("Подъезд", p.CAT_4_ENTRANCE),
                ("Двор", p.CAT_5_COURTYARD),
                ("Безопасность", p.CAT_6_SECURITY)
            ]
            if hasattr(p, "CAT_7_WALLS"): pool_base.append(("Стены", p.CAT_7_WALLS))
            if hasattr(p, "CAT_8_BALCONY"): pool_base.append(("Балкон", p.CAT_8_BALCONY))
            if hasattr(p, "CAT_9_LIGHT"): pool_base.append(("Свет", p.CAT_9_LIGHT))
            if hasattr(p, "CAT_10_STORAGE"): pool_base.append(("Холл", p.CAT_10_STORAGE))

        if cfg.enable_topic_rotation:
            rot_rng = random.Random(idx * 7919 + 101)
            cat_order = list(range(len(pool_base)))
            rot_rng.shuffle(cat_order)
            chosen_categories = [pool_base[i] for i in cat_order[:cfg.super_shorts_count]]
        else:
            chosen_categories = [pool_base[i % len(pool_base)] for i in range(cfg.super_shorts_count)]

        for cat_idx, (topic_name, pool) in enumerate(chosen_categories):
            raw_template = pool[(idx + cat_idx * 13) % len(pool)]
            rng = random.Random(idx * 10007 + cat_idx * 37 + 11)
            body = self._resolve_spintax(raw_template, rng)
            tag = self._format_tag("Суперкороткий", "Жилец", topic_name)
            revs.append(f"{tag} {body}")

        # 2. КОРОТКИЕ КАТЕГОРИИ (Geo-Injection: Метро, Шоссе, Парк, Набережная)
        target_names = facts.get("target_names", [])
        metro_clash = bool(metro_station and any(metro_station.lower() in t.lower() or (len(t) >= 4 and t.lower() in metro_station.lower()) for t in target_names))
        highway_clash = bool(highway_name and any(highway_name.lower() in t.lower() or (len(t) >= 4 and t.lower() in highway_name.lower()) for t in target_names))

        rng_short0 = random.Random(idx * 10037 + 23)
        if cfg.enable_hyperlocal and metro_station and not metro_clash and (idx % 2 == 0 or not has_park_near):
            # Geo-инъекция станции метро
            tag_infra = self._format_tag("Короткий", "Пешеход", f"Метро {metro_station}")
            metro_variants = [
                f"До станции метро {metro_station} спокойным шагом дохожу за несколько минут, дорога освещена.",
                f"Дойти пешком до метро {metro_station} можно буквально за десять минут, идти приятно и безопасно.",
                f"Станция метро {metro_station} находится в пешей доступности, добираться до центра города очень удобно."
            ]
            raw_infra = metro_variants[idx % len(metro_variants)]
        elif cfg.enable_hyperlocal and highway_name and not highway_clash and (idx % 3 == 0):
            # Geo-инъекция шоссе или проспекта
            tag_infra = self._format_tag("Короткий", "Автомобилист", f"Выезд на {highway_name}")
            hw_variants = [
                f"Выезд на {highway_name} удобный и быстрый, утром до работы доезжаем без нервов.",
                f"Развязка и прямой выезд на {highway_name} здорово экономят время при ежедневных поездках."
            ]
            raw_infra = hw_variants[idx % len(hw_variants)]
        elif cfg.enable_hyperlocal and has_water_near and hasattr(p, "SHORT_0_INFRA_WATER") and (idx % 2 == 1):
            # Geo-инъекция набережной / реки
            tag_infra = self._format_tag("Короткий", "Пешеход", "Набережная у дома")
            raw_infra = p.SHORT_0_INFRA_WATER[idx % len(p.SHORT_0_INFRA_WATER)]
        elif cfg.enable_hyperlocal and has_park_near:
            # Парк рядом
            tag_infra = self._format_tag("Короткий", "Пешеход", "Парк рядом")
            raw_infra = p.SHORT_0_INFRA_PARK[idx % len(p.SHORT_0_INFRA_PARK)]
        else:
            tag_infra = self._format_tag("Короткий", "Пешеход", "Инфраструктура")
            raw_infra = p.SHORT_0_INFRA_BASE[idx % len(p.SHORT_0_INFRA_BASE)]
        
        body_infra = self._resolve_spintax(raw_infra, rng_short0)
        revs.append(f"{tag_infra} {body_infra}")

        # Короткий 2: Качество / Потолки
        rng_short1 = random.Random(idx * 10039 + 47)
        if cfg.enable_hyperlocal and ceiling_height and float(ceiling_height) >= 3.0:
            tag_quality = self._format_tag("Короткий", "Новосел", "Высокие потолки")
            body_quality = f"Потолки {ceiling_height} метра дают колоссальное ощущение простора и света в комнатах."
        else:
            tag_quality = self._format_tag("Короткий", "Новосел", "Качество дома")
            raw_quality = p.SHORT_1_QUALITY[idx % len(p.SHORT_1_QUALITY)]
            body_quality = self._resolve_spintax(raw_quality, rng_short1)
        revs.append(f"{tag_quality} {body_quality}")

        # 3. СРЕДНИЕ ОТЗЫВЫ: РОЛЕВЫЕ МАСКИ С FACT-LOCKING И ОТДЕЛКОЙ
        if cfg.enable_personas:
            rng_med1 = random.Random(idx * 10061 + 71)
            rng_med2 = random.Random(idx * 10067 + 83)
            
            # Роль 1
            if cfg.vibe == "warm" or (idx % 2 == 0 and cfg.vibe != "pragmatic"):
                # Семья / Мама
                if has_stroller_room:
                    tag_p1 = self._format_tag("Средний", "Мама с коляской", "Колясочная и вход")
                    body_p1 = p.MED_FAMILY_STROLLER_ROOM[idx % len(p.MED_FAMILY_STROLLER_ROOM)]
                elif has_closed_yard:
                    tag_p1 = self._format_tag("Средний", "Мама с коляской", "Закрытый двор")
                    body_p1 = p.MED_FAMILY_CLOSED_YARD[idx % len(p.MED_FAMILY_CLOSED_YARD)]
                else:
                    tag_p1 = self._format_tag("Средний", "Мама с коляской", "Вход без порогов и площадка")
                    body_p1 = p.MED_FAMILY_BASE[idx % len(p.MED_FAMILY_BASE)]
            else:
                # Удаленщик
                tag_p1 = self._format_tag("Средний", "Удаленщик", "Тишина и интернет")
                body_p1 = p.MED_REMOTE_BASE[idx % len(p.MED_REMOTE_BASE)]
            
            body_p1 = self._resolve_spintax(body_p1, rng_med1)
            revs.append(f"{tag_p1} {body_p1}")

            # Роль 2 (С учетом реального типа отделки, если известен)
            if finish_type == "turnkey" and hasattr(p, "MED_FINISH_TURNKEY"):
                tag_p2 = self._format_tag("Средний", "Новосел", "Ремонт от застройщика")
                raw_p2 = p.MED_FINISH_TURNKEY[idx % len(p.MED_FINISH_TURNKEY)]
            elif finish_type == "pre_finish" and hasattr(p, "MED_FINISH_PREFINISH"):
                tag_p2 = self._format_tag("Средний", "Новосел", "Предчистовая отделка")
                raw_p2 = p.MED_FINISH_PREFINISH[idx % len(p.MED_FINISH_PREFINISH)]
            elif finish_type == "bare_concrete" and hasattr(p, "MED_FINISH_CONCRETE"):
                tag_p2 = self._format_tag("Средний", "Мастер ремонта", "Ремонт с нуля под себя")
                raw_p2 = p.MED_FINISH_CONCRETE[idx % len(p.MED_FINISH_CONCRETE)]
            elif has_parking and (idx % 2 == 1 or cfg.vibe == "pragmatic"):
                tag_p2 = self._format_tag("Средний", "Автомобилист", "Подземный паркинг")
                raw_p2 = p.MED_AUTO_PARKING[idx % len(p.MED_AUTO_PARKING)]
            elif has_concierge:
                tag_p2 = self._format_tag("Средний", "Жилец", "Консьерж-сервис")
                raw_p2 = p.MED_MGMT_CONCIERGE[idx % len(p.MED_MGMT_CONCIERGE)]
            else:
                tag_p2 = self._format_tag("Средний", "Мастер ремонта", "Стяжка и геометрия стен")
                raw_p2 = p.MED_TECH_BASE[idx % len(p.MED_TECH_BASE)]

            body_p2 = self._resolve_spintax(raw_p2, rng_med2)
            revs.append(f"{tag_p2} {body_p2}")
        else:
            tag_m1 = self._format_tag("Средний", "Жилец", "Отделка")
            tag_m2 = self._format_tag("Средний", "Жилец", "УК и сервис")
            revs.append(f"{tag_m1} {p.MED_TECH_BASE[idx % len(p.MED_TECH_BASE)]}")
            revs.append(f"{tag_m2} {p.MED_FAMILY_BASE[idx % len(p.MED_FAMILY_BASE)]}")

        # 4. ДЛИННЫЙ НАРРАТИВ (3 предложения со спин-синтаксисом)
        rng_l1 = random.Random(idx * 10091 + 97)
        rng_l2 = random.Random(idx * 10093 + 103)
        rng_l3 = random.Random(idx * 10099 + 109)

        tag_long = self._format_tag("Развернутый", "Семья с ребенком", "Опыт проживания")
        if cfg.enable_hyperlocal and district and len(district) >= 3 and district.lower() not in ["msk", "spb", "perm"]:
            l1_raw = f"Квартиру искали именно в районе {district}, чтобы жить в привычном окружении и не тратить часы на поездки."
        else:
            l1_raw = p.LONG_S1_BASE[idx % len(p.LONG_S1_BASE)]

        s2_pool = list(p.LONG_S2_BASE)
        if has_closed_yard:
            s2_pool.append(p.LONG_S2_CLOSED_YARD)
        if has_parking:
            s2_pool.append(p.LONG_S2_PARKING)

        l2_raw = s2_pool[(idx // len(p.LONG_S1_BASE)) % len(s2_pool)]
        l3_raw = p.LONG_S3_BASE[(idx // (len(p.LONG_S1_BASE) * len(s2_pool))) % len(p.LONG_S3_BASE)]

        l1 = self._resolve_spintax(l1_raw, rng_l1)
        l2 = self._resolve_spintax(l2_raw, rng_l2)
        l3 = self._resolve_spintax(l3_raw, rng_l3)

        revs.append(f"{tag_long} {l1} {l2} {l3}")

        # 5. СТРОГАЯ ВАЛИДАЦИЯ С УЧЕТОМ ФАКТОВ
        target_names = facts.get("target_names", [])
        self.validator.validate_batch(revs, forbidden_names=target_names, facts=facts)

        return revs

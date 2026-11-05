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

    def generate_complex_reviews(self, idx: int, facts: Optional[Dict[str, Any]] = None) -> List[str]:
        facts = facts or {}
        has_parking = bool(facts.get("has_parking", False))
        district = str(facts.get("district", "")).strip()
        ceiling_height = facts.get("ceiling_height")

        p = self.preset
        cfg = self.config
        revs = []

        # 1. Суперкороткие (7 штук с уникальными стартерами)
        super_short_pool = [
            p.CAT_0_WINDOWS,
            p.CAT_1_HEATING,
            p.CAT_2_WATER,
            p.CAT_3_ELEVATORS,
            p.CAT_4_ENTRANCE,
            p.CAT_5_COURTYARD,
            p.CAT_6_SECURITY
        ]
        for cat_idx in range(cfg.super_shorts_count):
            pool = super_short_pool[cat_idx % len(super_short_pool)]
            revs.append(f"[Суперкороткий] {pool[idx % len(pool)]}")

        # 2. Короткие
        revs.append(f"[Короткий] {p.SHORT_0_INFRA[idx % len(p.SHORT_0_INFRA)]}")
        
        # Если включена гиперлокальность и известны потолки
        if cfg.enable_hyperlocal and ceiling_height and float(ceiling_height) >= 3.0:
            revs.append(f"[Короткий] Потолки {ceiling_height} метра дают колоссальное ощущение простора и света в комнатах.")
        else:
            revs.append(f"[Короткий] {p.SHORT_1_QUALITY[idx % len(p.SHORT_1_QUALITY)]}")

        # 3. Средние (Ролевые маски или Нейтральные)
        if cfg.enable_personas:
            # Чередуем роли по остатку от деления индекса
            # Четные дома: Мама + Технарь
            # Нечетные дома: Удаленка + Автомобилист (или нейтрал без авто)
            if idx % 2 == 0:
                p1_pool = p.MED_PERSONA_FAMILY
                p2_pool = p.MED_PERSONA_TECH
            else:
                p1_pool = p.MED_PERSONA_REMOTE
                p2_pool = p.MED_PERSONA_AUTO if has_parking else p.MED_PERSONA_FAMILY

            revs.append(f"[Средний] {p1_pool[idx % len(p1_pool)]}")
            revs.append(f"[Средний] {p2_pool[idx % len(p2_pool)]}")
        else:
            revs.append(f"[Средний] {p.MED_0_FLAT_NEUTRAL[idx % len(p.MED_0_FLAT_NEUTRAL)]}")
            revs.append(f"[Средний] {p.MED_1_MGMT_NEUTRAL[idx % len(p.MED_1_MGMT_NEUTRAL)]}")

        # 4. Длинный нарратив
        # Если включена гиперлокальность и есть понятный район
        if cfg.enable_hyperlocal and district and len(district) >= 3 and district.lower() not in ["msk", "spb"]:
            l1 = f"Квартиру искали именно в районе {district}, чтобы жить в привычном окружении и не тратить часы на поездки."
        else:
            l1 = p.LONG_S1_BASE[idx % len(p.LONG_S1_BASE)]

        long_s2_pool = p.LONG_S2_BASE + (["Лифты спускаются прямо на уровень паркинга, что колоссально экономит время в холодные месяцы."] if has_parking else [])
        l2 = long_s2_pool[(idx // len(p.LONG_S1_BASE)) % len(long_s2_pool)]
        l3 = p.LONG_S3_BASE[(idx // (len(p.LONG_S1_BASE) * len(long_s2_pool))) % len(p.LONG_S3_BASE)]
        revs.append(f"[Развернутый] {l1} {l2} {l3}")

        # Quality Gate validation
        target_names = facts.get("target_names", [])
        self.validator.validate_batch(revs, forbidden_names=target_names)

        return revs

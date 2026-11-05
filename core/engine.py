from typing import Dict, Any, List, Optional
from core.validator import SlopValidator

class HumanWriterEngine:
    def __init__(self, preset_module, validator: Optional[SlopValidator] = None):
        self.preset = preset_module
        self.validator = validator or SlopValidator()

    def generate_complex_reviews(self, idx: int, facts: Optional[Dict[str, Any]] = None) -> List[str]:
        facts = facts or {}
        has_parking = bool(facts.get("has_parking", False))

        p = self.preset
        revs = []

        # 1. 7 Super Shorts (детерминированная ротация без повторов стартеров)
        revs.append(f"[Суперкороткий] {p.CAT_0_WINDOWS[idx % len(p.CAT_0_WINDOWS)]}")
        revs.append(f"[Суперкороткий] {p.CAT_1_HEATING[idx % len(p.CAT_1_HEATING)]}")
        revs.append(f"[Суперкороткий] {p.CAT_2_WATER[idx % len(p.CAT_2_WATER)]}")
        revs.append(f"[Суперкороткий] {p.CAT_3_ELEVATORS[idx % len(p.CAT_3_ELEVATORS)]}")
        revs.append(f"[Суперкороткий] {p.CAT_4_ENTRANCE[idx % len(p.CAT_4_ENTRANCE)]}")
        revs.append(f"[Суперкороткий] {p.CAT_5_COURTYARD[idx % len(p.CAT_5_COURTYARD)]}")
        revs.append(f"[Суперкороткий] {p.CAT_6_SECURITY[idx % len(p.CAT_6_SECURITY)]}")

        # 2. 2 Shorts
        revs.append(f"[Короткий] {p.SHORT_0_INFRA[idx % len(p.SHORT_0_INFRA)]}")
        revs.append(f"[Короткий] {p.SHORT_1_QUALITY[idx % len(p.SHORT_1_QUALITY)]}")

        # 3. 2 Mediums
        revs.append(f"[Средний] {p.MED_0_FLAT[idx % len(p.MED_0_FLAT)]}")

        # Fact-locked parking
        med1_pool = p.MED_1_BASE + ([p.MED_1_PARKING] if has_parking else [])
        revs.append(f"[Средний] {med1_pool[idx % len(med1_pool)]}")

        # 4. 1 Long
        long_s2_pool = p.LONG_S2_BASE + ([p.LONG_S2_PARKING] if has_parking else [])
        l1 = p.LONG_S1[idx % len(p.LONG_S1)]
        l2 = long_s2_pool[(idx // len(p.LONG_S1)) % len(long_s2_pool)]
        l3 = p.LONG_S3[(idx // (len(p.LONG_S1) * len(long_s2_pool))) % len(p.LONG_S3)]
        revs.append(f"[Развернутый] {l1} {l2} {l3}")

        # Quality Gate validation
        target_names = facts.get("target_names", [])
        self.validator.validate_batch(revs, forbidden_names=target_names)

        return revs

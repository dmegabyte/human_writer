import re
from typing import Dict, Any
import pandas as pd

class FactExtractor:
    """Извлекает проверенные физические факты из карточки ЖК и аналитики neiro."""

    @staticmethod
    def extract_from_row(row: Any) -> Dict[str, Any]:
        d_info = str(row.get("detail_info", "")).lower()
        neiro = str(row.get("neiro", "")).lower()
        all_text = f"{d_info} {neiro}"

        # 1. Паркинг
        p_col = row.get("parking")
        has_parking = bool(
            (pd.notna(p_col) and int(p_col) == 1) or
            "паркинг" in all_text or
            "подземн" in all_text
        )

        # 2. Закрытый двор / двор без машин
        has_closed_yard = bool(
            "без машин" in all_text or
            "закрытая территория" in all_text or
            "закрытый двор" in all_text
        )

        # 3. Колясочная
        has_stroller_room = bool("колясочн" in all_text)

        # 4. Консьерж
        has_concierge = bool("консьерж" in all_text)

        # 5. Охрана / КПП
        has_security = bool("охрана" in all_text or "охранн" in all_text)

        # 6. Парк или сквер рядом
        p_near = row.get("park_near")
        has_park_near = bool(
            (pd.notna(p_near) and float(p_near) == 1.0) or
            "парк" in d_info or
            "сквер" in d_info
        )

        # 7. Высокие потолки (>= 3.0м)
        ceil = row.get("min_ceiling_height")
        has_high_ceil = bool(pd.notna(ceil) and float(ceil) >= 3.0)
        ceiling_val = float(ceil) if has_high_ceil else None

        # 8. Район / локация
        district = str(row.get("district", "")).strip()

        # 9. Название комплекса для проверки на запрет утечек
        raw_name = str(row.get("name", ""))
        clean_name = re.sub(r"^(ЖК|Жилой комплекс|МФК|Квартал|Дом)\s+", "", raw_name, flags=re.I).strip()

        return {
            "has_parking": has_parking,
            "has_closed_yard": has_closed_yard,
            "has_stroller_room": has_stroller_room,
            "has_concierge": has_concierge,
            "has_security": has_security,
            "has_park_near": has_park_near,
            "has_high_ceil": has_high_ceil,
            "ceiling_height": ceiling_val,
            "district": district,
            "target_names": [raw_name, clean_name]
        }

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

        # 9. Метро (Geo-Injection)
        metro_station = None
        raw_text_case = f"{str(row.get('detail_info', ''))} {str(row.get('neiro', ''))}"
        metro_bad = {
            "также", "особое", "купить", "для", "здесь", "все", "кроме", "большой",
            "высотный", "город", "дом", "новый", "станция", "метро", "минут", "пешком",
            "транспортом", "шагом", "находится", "рядом", "около", "время", "доступности",
            "предусмотрено", "планируется", "расположена", "будет", "проектом", "минутах",
            "шаговой", "удобно", "можно", "открыта", "строится", "строительство", "расстояние",
            "комплекс", "жилой", "проект", "район", "квартал", "пешей", "близости", "добраться",
            "апартаменты", "благодаря", "ближайшая", "большие", "будущим", "введен", "ввод",
            "вестибюли", "внутри", "вместе", "высокий", "выезд", "главный", "деревня", "другие",
            "жители", "жителям", "здание", "каждый", "корпус", "крупный", "любой", "многие",
            "наличие", "несколько", "общая", "один", "основной", "первый", "пешеходный", "площадь",
            "поездка", "позволяет", "позволит", "поможет", "прекрасный", "прогулка", "развитая",
            "различные", "расположен", "сдача", "северный", "современный", "составляет", "станет",
            "стоимость", "территория", "удобная", "хорошая", "центр", "южный", "через", "прямо"
        }
        metro_patterns = [
            r'(?:до\s+метро|станци[ия]\s+метро|м\.)\s*[«\"]?([А-ЯЁ][а-яё\-]+(?:\s+[А-ЯЁ][а-яё\-]+)?)[»\"]?',
            r'метро\s+[«\"]([А-ЯЁ][а-яё\-]+(?:\s+[А-ЯЁ][а-яё\-]+)?)[»\"]'
        ]
        for pat in metro_patterns:
            m = re.search(pat, raw_text_case)
            if m:
                cand = m.group(1).strip()
                if len(cand) >= 4 and cand.lower() not in metro_bad:
                    metro_station = cand
                    break

        # 10. Шоссе / Проспект (Geo-Injection)
        street_raw = str(row.get("street", ""))
        highway_name = None
        m_hw = re.search(r'([А-ЯЁ][а-яё\-]+(?:\s+[А-ЯЁ][а-яё\-]+)?\s+шоссе)', street_raw)
        if m_hw:
            highway_name = m_hw.group(1).strip()
        else:
            m_pr = re.search(r'(проспект\s+[А-ЯЁ][а-яё\-]+|[А-ЯЁ][а-яё\-]+\s+проспект|пр-т\s+[А-ЯЁ][а-яё\-]+)', street_raw, re.IGNORECASE)
            if m_pr:
                highway_name = m_pr.group(1).strip()

        # 11. Водоем / набережная рядом
        w_near = row.get("water_near")
        s_near = row.get("sea_near")
        has_water_near = bool(
            (pd.notna(w_near) and float(w_near) == 1.0) or
            (pd.notna(s_near) and float(s_near) == 1.0) or
            "набережн" in all_text or
            "у воды" in all_text or
            "река" in d_info or
            "пруд" in d_info
        )

        # 12. Тип отделки (разговорный, без технических штампов)
        finish_type = None
        if "под ключ" in all_text or "чистов" in all_text or "готовый ремонт" in all_text or "готовой отделк" in all_text:
            finish_type = "turnkey"        # готовый ремонт от застройщика
        elif "предчистов" in all_text or "white" in all_text or "под чистовую" in all_text:
            finish_type = "pre_finish"     # предчистовая (стены и полы готовы под косметику)
        elif "чернов" in all_text or "без отделки" in all_text or "свободн" in all_text or "в бетоне" in all_text:
            finish_type = "bare_concrete"  # в бетоне под свой ремонт с нуля

        # 13. Название комплекса для проверки на запрет утечек
        raw_name = str(row.get("name", ""))
        clean_name = re.sub(r"^(ЖК|Жилой комплекс|МФК|Квартал|Дом)\s+", "", raw_name, flags=re.I).strip()

        return {
            "has_parking": has_parking,
            "has_closed_yard": has_closed_yard,
            "has_stroller_room": has_stroller_room,
            "has_concierge": has_concierge,
            "has_security": has_security,
            "has_park_near": has_park_near,
            "has_water_near": has_water_near,
            "has_high_ceil": has_high_ceil,
            "ceiling_height": ceiling_val,
            "metro_station": metro_station,
            "highway_name": highway_name,
            "finish_type": finish_type,
            "district": district,
            "target_names": [raw_name, clean_name]
        }

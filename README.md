# human_writer ✍️
**Универсальный модульный движок генерации естественных текстов и отзывов без слопа и галлюцинаций.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.10+](https://img.shields.io/badge/python-3.10+-brightgreen.svg)](https://www.python.org/)
[![Speed: 25k in <1s](https://img.shields.io/badge/speed-25k%20in%20%3C1s-orange.svg)](#)

---

## 🎯 Назначение и проблема

При массовом создании тысяч отзывов, карточек или описаний через LLM (OpenAI, Gemini, Claude, Llama):
1. **Галлюцинации и усталость (LLM Slop):** Нейросети скатываются в штампы (*«Для нас важно...»*, *«Стоит отметить...»*, *«Порадовало, что...»*), страдательный залог и неестественный бюрократический тон.
2. **Фактологические ошибки:** LLM придумывает паркинги, метро или консьержей там, где их нет.
3. **Медленно и дорого:** Сетевые запросы на 20 000+ объектов занимают часы и съедают сотни долларов на токенах.

**`human_writer` решает это фундаментально:**
- ⚡ **Скорость:** 25 000 уникальных текстов менее чем за 1 секунду на обычном CPU.
- 🔒 **Fact-Locking Matrix:** Физическая невозможность приписать несуществующие удобства.
- 🛡️ **Zero-Slop Shield:** Полный запрет канцеляризмов, длинных тире (`—`, `–`) и утечек названия ЖК в тексте.
- 🎛️ **Готов к UI/REST API:** Настройки экспортируются в JSON и на лету управляются из административного интерфейса.

---

## 📂 Структура репозитория

```text
human_writer/
├── core/
│   ├── config.py           # Конфигурация WriterConfig (to_dict, from_dict, JSON)
│   ├── engine.py           # Движок сборки текстов HumanWriterEngine
│   ├── fact_extractor.py   # Извлечение фактов из карточек и аналитики
│   └── validator.py        # Валидатор качества SlopValidator (0 штампов, 0 тире)
│
├── presets/
│   └── real_estate.py      # Пресет живого языка для недвижимости (166 шаблонов)
│
├── configs/
│   └── real_estate_default.json # Дефолтный JSON-конфиг
│
└── exporters/              # Экспорт в Google Sheets и JSONL
```

---

## 🎛️ Руководство для разработчика UI (Параметры и Контролы)

Класс `WriterConfig` в [`core/config.py`](core/config.py) сериализуется в JSON и десериализуется обратно одной строчкой.

### Сводная таблица параметров для UI-формы:

| Параметр в API | Тип данных | Дефолт | UI Контрол | Описание для пользователя |
| :--- | :---: | :---: | :--- | :--- |
| `enable_hyperlocal` | `boolean` | `true` | **Switch / Чекбокс** | Подмешивать факты из карточки (высота потолков, район, улица) |
| `enable_personas` | `boolean` | `true` | **Switch / Чекбокс** | Использовать ролевые маски (мама, автомобилист, технарь, удаленщик) |
| `enable_persona_tags` | `boolean` | `true` | **Switch / Чекбокс** | Выводить теги в начале отзыва: `[Тип \| Роль \| Тема]` |
| `enable_burstiness` | `boolean` | `true` | **Switch / Чекбокс** | Живой рваный ритм речи (чередование коротких и емких фраз) |
| `enable_spintax` | `boolean` | `true` | **Switch / Чекбокс** | Мультипликатор синонимов `{А\|Б\|В}` (тысячи уникальных формулировок) |
| `enable_topic_rotation` | `boolean` | `true` | **Switch / Чекбокс** | Перемешивание порядка тем от дома к дому (защита от цикличности) |
| `vibe` | `string` | `"balanced"` | **Dropdown (Select)** | Эмоциональный тон: `balanced` (баланс), `pragmatic` (сухой технарь), `warm` (семейный уют) |
| `ban_dashes` | `boolean` | `true` | **Switch / Чекбокс** | Строгий запрет длинных и средних тире (`—`, `–`) |
| `ban_target_names` | `boolean` | `true` | **Switch / Чекбокс** | Запрет названия ЖК в тексте (жители говорят «в доме», «у нас») |
| `slang_level` | `string` | `"medium"` | **Dropdown (Select)** | Уровень разговорности: `none`, `medium`, `high` |
| `preset_name` | `string` | `"real_estate"`| **Dropdown (Select)** | Отраслевой пресет: `real_estate`, `ecommerce`, `auto` |
| `super_shorts_count` | `integer` | `7` | **Number / Slider** | Количество супер-коротких отзывов на карточку |
| `shorts_count` | `integer` | `2` | **Number / Slider** | Количество коротких отзывов |
| `mediums_count` | `integer` | `2` | **Number / Slider** | Количество средних ролевых отзывов |
| `longs_count` | `integer` | `1` | **Number / Slider** | Количество развернутых комплексных отзывов |
| `stop_words` | `list[str]`| *список* | **Tag Input / Chips** | Список стоп-слов, которые валидатор блокирует на лету |

---

## 🔌 Пример интеграции в REST API (FastAPI / Flask)

Разработчик бэкенда может легко реализовать управление настройками через API:

```python
from fastapi import FastAPI, HTTPException
from core.config import WriterConfig
from core.engine import HumanWriterEngine
from presets.real_estate import REAL_ESTATE_PRESET

app = FastAPI(title="HumanWriter API")

# Текущий рабочий конфиг
current_config = WriterConfig.load_json("configs/real_estate_default.json")

@app.get("/api/config")
def get_config():
    """Получение текущих настроек для заполнения формы в UI."""
    return current_config.to_dict()

@app.post("/api/config")
def update_config(payload: dict):
    """Сохранение настроек из UI формы."""
    global current_config
    current_config = WriterConfig.from_dict(payload)
    return {"status": "ok", "config": current_config.to_dict()}

@app.post("/api/generate")
def generate_reviews(payload: dict):
    """
    Генерация батча отзывов для карточки.
    payload: {
        "index": 12,
        "facts": {
            "has_parking": true,
            "has_closed_yard": true,
            "has_stroller_room": false,
            "has_concierge": false,
            "has_park_near": true,
            "ceiling_height": 3.1
        }
    }
    """
    engine = HumanWriterEngine(preset_module=REAL_ESTATE_PRESET, config=current_config)
    facts = payload.get("facts", {})
    idx = payload.get("index", 0)
    
    reviews = engine.generate_complex_reviews(idx=idx, facts=facts)
    return {"status": "ok", "count": len(reviews), "reviews": reviews}
```

---

## 🧠 Fact-Locking Matrix (Входные данные объекта)

Чтобы исключить любые небылицы, генератор опирается на словарь фактов `facts`.

Если факт равен `False` или `None`, фразы на эту тему **математически не попадут в выборку**:

```python
facts = {
    "has_parking": True,          # Есть паркинг (подземный или крытый)
    "has_closed_yard": True,      # Двор закрыт от машин
    "has_stroller_room": False,   # Нет отдельной колясочной
    "has_concierge": False,       # Нет консьержа / охраны
    "has_park_near": True,        # Рядом есть парк или сквер
    "has_water_near": True,       # Рядом есть набережная / река
    "metro_station": "Смоленская",# Станция метро в пешей доступности
    "highway_name": "Новый Арбат",# Шоссе / проспект для автомобилиста
    "finish_type": "turnkey",     # Тип отделки: "turnkey" (с готовым ремонтом), "pre_finish" (предчистовая, без вайтбокса), "bare_concrete" (в бетоне с нуля)
    "district": "Академический",  # Район (для гиперлокальности)
    "ceiling_height": 3.05        # Высота потолков в метрах
}
```

Для табличных данных (например, Pandas DataFrame из парсинга новостроек) используется автоматический экстрактор:

```python
from core.fact_extractor import FactExtractor

facts = FactExtractor.extract_from_row(df_row)
```

---

## 🛡️ Slop-Shield Валидатор

Каждый отзыв перед выдачей проходит автоматическую проверку:
1. **0 стоп-слов:** автоматическая браковка фраз со штампами (*«для нас важно»*, *«стоит отметить»*, *«данный объект»*, *«лотов»*).
2. **0 тире:** гарантированное отсутствие длинных (`—`) и средних (`–`) книжных тире.
3. **0 утечек названия:** строгий regex-контроль, запрещающий упоминать официальное имя ЖК внутри отзыва (жильцы говорят *«в подъезде»*, *«во дворе»*, а не *«в ЖК По ул. Ленина, 5»*).

---

## 🚀 Быстрый старт в консоли

```bash
# Клонирование репозитория
git clone https://github.com/dmegabyte/human_writer.git
cd human_writer

# Проверка базовой генерации
python3 -c "
from core.engine import HumanWriterEngine
from presets.real_estate import REAL_ESTATE_PRESET
from core.config import WriterConfig

cfg = WriterConfig(enable_persona_tags=True)
engine = HumanWriterEngine(preset_module=REAL_ESTATE_PRESET, config=cfg)

reviews = engine.generate_complex_reviews(idx=0, facts={'has_parking': True, 'has_park_near': True})
for r in reviews:
    print(r)
"
```

---

## 📄 Лицензия

MIT License. Свободно для коммерческого и некоммерческого использования.

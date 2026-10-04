# Инструкции для Босса: Earth Studio, ключ Gemini, S3

## 1. Google Earth Studio — два пролёта для фильма

Сайт: https://earth.google.com/studio/ (только Chrome на ноутбуке). Если при первом входе попросит «Request access» — заполни форму, доступ обычно дают сразу.

### Пролёт 1 — вдоль канала от моря к Safa Park (открытие фильма)

1. **Blank project ▾** → в выпадашке выбери **Quick Start → Point to Point**.
2. **Settings:** Name `Canal_Flyover`, **Dimensions — Custom: 1080 × 1920** (вертикаль), Duration **10 s**, FPS **30**.
3. Карта: в поиске набери **Jumeirah Beach, Dubai** → это точка A (старт). В поле **Altitude** поставь ≈ **300 m**, наклон камеры (Tilt) ≈ **60°**, курс вдоль канала в сторону Safa Park.
4. Точка B (финиш): поиск **Al Safa Park, Dubai** → Altitude ≈ **120 m**, Tilt ≈ **55°**.
5. **Attributes** (справа) → включи **Time of Day** → поставь **17:45** (золотой час Дубая). Это даёт длинные тени и тёплый свет.
6. **Overlays / Labels:** всё выключить — никаких подписей на карте.
7. Прокрути таймлайн: камера должна плавно лететь над водой, Canal Front появляется справа у парка. Если дёргается — в Animation включи **Ease In/Out** на ключевых кадрах.

### Пролёт 2 — облёт Canal Front Residences (пресет Test Flight A)

1. **Quick Start → Orbit**.
2. В поиске: **Canal Front Residences, Al Wasl, Dubai** (это центр орбиты — Target).
3. **Settings:** `CanalFront_Orbit`, 1080 × 1920, 10 s, 30 fps.
4. Параметры орбиты: **Radius ≈ 250 m**, **Altitude 150 m → 60 m** (анимируй: первый ключевой кадр 150, последний 60), **Rotation ≈ 70°** (не полный круг), Tilt ≈ −15°.
5. Time of Day **17:45**, подписи выключены.

### Рендер и перенос в Descript (для обоих)

1. **Render** (справа вверху) → Format **Image Sequence (JPEG)**, Quality **High**, остальное по умолчанию → **Start**. Рендер идёт в браузере, 5–10 минут на ролик; вкладку не закрывать. Скачается zip с кадрами.
2. На маке: распаковать → **QuickTime Player → File → Open Image Sequence…** → выбрать папку с кадрами → Frame rate **30** → Choose → **File → Save** → `canal_flyover.mov` (и `canalfront_orbit.mov`).
3. Открыть проект Descript **Billionaire Row** → перетащить оба .mov в панель **Media** (в папку Photos или рядом).

Если Earth Studio не хочет отдавать вертикаль — рендери 1920 × 1080, я обрежу под вертикаль в Descript (камера по центру кадра, так что потерь не будет).

## 2. Ключ Gemini API (для Ноды 4 — Veo 3.1)

1. https://aistudio.google.com → войти Google-аккаунтом → слева **Get API key** → **Create API key** → выбрать (или создать) проект Google Cloud.
2. **Важно: Veo работает только на платном тарифе.** Если ключ создан в бесплатном проекте — в https://console.cloud.google.com → **Billing** привязать карту к этому проекту. Без этого генерация вернёт ошибку доступа.
3. Скопировать ключ (строка вида `AIza…`). **Никуда в чат не вставлять.**

### Куда положить в n8n

n8n → левое меню **Credentials** → **Add credential** → в поиске **Header Auth** →
- **Credential name:** `Gemini API`
- **Name (header):** `x-goog-api-key`
- **Value:** ключ
→ **Save**.

Я в Ноде 4 (HTTP Request) выберу эту credential — ключ в теле воркфлоу светиться не будет.

## 3. Timeweb S3 — уже есть

В n8n лежит credential **«Timeweb S3»** (тип S3, id `ygC0mmCU7vDdHok8`) — с летнего проекта зеркалирования медиа. Ничего заводить не нужно. Вопрос один: **в какой бакет класть видео** — в существующий `menaoffplan-media` с префиксом `video-prod/{project}/…` (по Build Kit) или завести отдельный бакет `video-prod`? По умолчанию возьму существующий бакет с префиксом.

## 4. Фото квартиры — уже в Descript

Из zip (44 фото портала, 1024 px) отобраны и загружены в проект Descript в папку **Photos** 14 кадров под шот-лист:

| Файл | Для какого пролёта |
|---|---|
| 01_living_wide | гостиная — наезд к окну (кадр 3) |
| 02_living_sofa_windows | гостиная, запасной ракурс |
| 03_kitchen_dining_wide | кухня + столовая — боковое скольжение (кадр 4) |
| 04_kitchen_counter | кухня крупно, запасной |
| 05_bedroom_window | спальня — к окну с видом на башни (кадр 5) |
| 06_bath_tub | ванна |
| 07_bathroom_shower | душ |
| 08_laundry | лондри |
| 09_balcony_view_towers | вид с балкона на башни |
| 10_skyline_yacht | Billionaire Row — наезд на башни с яхтой (кадр 6) |
| 11_building_canal_bridge | дом через канал с мостом Tolerance — фасад |
| 12_promenade_towers | набережная — долли вперёд (кадр 8) |
| 13_building_exterior | фасад снизу |
| 14_canal_marine_station | канал от станции Safa Park |

Ограничение: 1024 px — под вертикаль 1080 × 1920 будет апскейл. Если найдутся оригиналы с камеры (2000+ px) — заменим, качество пролётов заметно вырастет.

**Генерация пролётов в приложении Descript (Creator):** открыть проект → Media → выбрать фото → **Generate → Image to video** → вставить промпт из шот-листа (`billionaire-row-film-v1.md`, раздел «Шот-лист v4») → длительность 5–6 с. Клипы остаются в Media — Claude их увидит и соберёт v4.

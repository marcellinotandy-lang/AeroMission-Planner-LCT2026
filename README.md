# AeroMission Planner

**AeroMission Planner** — сервис планирования и распределения беспилотных авиационных работ для кейса **ЛЦТ 2026 / Геоскан**.

Решение превращает заявку на авиационные работы в набор индивидуальных миссий БВС: строит галсы съемки по полигону, учитывает разрешенное воздушное пространство, no-fly зоны, ветер, резервные посадочные площадки, парк дронов и ограничение по времени. Результат можно посмотреть в браузере и выгрузить в **GeoJSON/KML**.

## Что реализовано

- веб-прототип без внешних картографических API-ключей;
- backend API на FastAPI + Pydantic-схемы входа/выхода;
- построение lawnmower-галсов по рабочей зоне `survey_area ∩ allowed_airspace - no_fly_zones`;
- учет типов съемки: `RGB`, `multispectral`, `IR`, `LiDAR`, `geophysical`;
- распределение полос между БВС по трем режимам: `min_time`, `min_airtime`, `balanced`;
- безопасный транзит вокруг запретных зон;
- проверка выполнимости по запасу батареи и дедлайну;
- экспорт маршрутов и точек в GeoJSON/KML;
- CI на GitHub Actions и расширенные `pytest`-проверки.

## Быстрый запуск

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

Открыть в браузере: `http://localhost:8000`.

Альтернатива через Docker:

```bash
docker compose up --build
```

## Тесты

```bash
pytest -q
```

Тесты проверяют доступность API, построение демо-миссий, три режима оптимизации, экспорт GeoJSON/KML, реакцию на жесткий дедлайн и отсутствие пересечения маршрутов с no-fly зонами.

## Структура

```text
backend/app/main.py                  FastAPI, статический фронт, export API
backend/app/models.py                Pydantic-схемы сценария и результата
backend/app/planner/core.py          галсы, assignment, метрики, feasibility
backend/app/planner/pathfinding.py   безопасный обход no-fly зон
backend/app/planner/exporters.py     GeoJSON/KML
frontend/                            браузерный прототип без сборки
examples/demo_scenario.json          демонстрационный сценарий
docs/                                документация, презентация, демо-экспорты, self-review
tests/                               regression/QA tests
```

## API

- `GET /api/health` — проверка сервиса.
- `POST /api/plan` — построить план по JSON-сценарию.
- `POST /api/export/geojson` — экспорт результата планирования.
- `POST /api/export/kml` — экспорт результата планирования.

## Что сдавать

- Репозиторий: `https://github.com/marcellinotandy-lang/AeroMission-Planner-LCT2026`
- Документация: `docs/AeroMission_Planner_Documentation.pdf` или `docs/documentation.md`
- Презентация: `docs/AeroMission_Planner_Presentation.pdf` / `.pptx`
- Прототип: локальный запуск из README, после запуска `http://localhost:8000`
- Дополнительно: `docs/demo_plan_result.json`, `docs/demo_routes.geojson`, `docs/demo_routes.kml`, `docs/llm_judge_review.md`

## Ограничения MVP

Для хакатонного MVP рельеф и высотные препятствия задаются как полигональные ограничения. Камеры сведены к инженерной ширине покрытия по типу съемки. Для промышленной версии можно добавить DEM-рельеф, каталог камер/полезных нагрузок Геоскан, профиль энергопотребления и экспорт под конкретные форматы автопилотов.

# Данные для формы сдачи ЛЦТ 2026

Команда: `#ЕСТЬТАЛАНТ`

## Поля формы

- **Репозиторий:** https://github.com/marcellinotandy-lang/AeroMission-Planner-LCT2026
- **Документация:** `docs/AeroMission_Planner_Documentation.pdf` или `docs/documentation.md`
- **Презентация:** `docs/AeroMission_Planner_Presentation.pdf` / `docs/AeroMission_Planner_Presentation.pptx`
- **Прототип:** локальный FastAPI-прототип из репозитория, после запуска открыть `http://localhost:8000`
- **Дополнительные материалы:** `docs/demo_plan_result.json`, `docs/demo_routes.geojson`, `docs/demo_routes.kml`, `docs/QA_REPORT.md`

## Проверка перед отправкой

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

Открыть: http://localhost:8000

## Короткое описание для комментария к сдаче

AeroMission Planner — веб-сервис для планирования и распределения беспилотных авиационных работ. Сервис строит галсы съемки, учитывает воздушные ограничения и no-fly зоны, распределяет работу между БВС по времени/налету/балансу, проверяет выполнимость и экспортирует индивидуальные миссии в GeoJSON/KML.

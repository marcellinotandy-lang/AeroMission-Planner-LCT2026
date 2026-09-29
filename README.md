# AeroMission Planner

**AeroMission Planner** — сервис планирования и распределения беспилотных авиационных работ для кейса ЛЦТ 2026 / Геоскан.

Решение превращает заявку на авиационные работы в набор индивидуальных миссий БВС: строит галсы съёмки, учитывает разрешённое воздушное пространство, бесполётные зоны, стартовые и резервные площадки, ветер, ресурс батареи, дедлайн и состав парка.

## Что реализовано

- backend API на FastAPI;
- Pydantic-схемы входных данных и результата;
- генерация lawnmower-галсов по полигону работ;
- учёт allowed airspace и no-fly зон;
- safe routing вокруг запретных зон;
- распределение работ между БВС;
- 3 режима оптимизации: `min_time`, `min_airtime`, `balanced`;
- проверка выполнимости по времени и ресурсу;
- экспорт в GeoJSON и KML;
- браузерный Mission Control UI;
- тесты API, планировщика и экспортов.

## Mission Control UI

Финальная версия интерфейса оформлена как операторский экран:

- центральная карта с зонами, галсами и маршрутами;
- левая панель параметров миссии;
- верхние KPI по плану;
- правая панель валидации и предупреждений;
- индекс безопасности;
- нижний таймлайн загрузки флота;
- экспорт рассчитанного плана в GeoJSON/KML.

Полный обновлённый пакет с финальными исходниками, презентацией и документацией лежит в Google Drive:

https://drive.google.com/drive/folders/1N4fHkZ5UFOO86H7pKiWt5BcRGy-I6NFk

## Демо-сценарий

В финальном демо используется парк из 10 БВС: Геоскан 201, Геоскан 801 и Геоскан Gemini. Демо показывает распределение по флоту, обход no-fly зон, расчёт makespan, суммарного налёта, покрытия, галсов и статуса выполнимости.

## Быстрый запуск

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

Открыть в браузере: `http://localhost:8000`.

## Тесты

```bash
pytest -q
```

Финальная локальная проверка: **7/7 passed**.

## API

- `GET /api/health` — проверка сервиса.
- `POST /api/plan` — построить план по JSON-сценарию.
- `POST /api/export/geojson` — экспорт результата планирования в GeoJSON.
- `POST /api/export/kml` — экспорт результата планирования в KML.

## Структура

```text
backend/app/main.py                FastAPI API + frontend hosting
backend/app/models.py              Pydantic-модели входа/выхода
backend/app/planner/core.py        галсы, assignment, feasibility
backend/app/planner/pathfinding.py safe routing вокруг no-fly зон
backend/app/planner/exporters.py   GeoJSON/KML
frontend/                          Mission Control UI
examples/demo_scenario.json        демонстрационный сценарий
docs/                              документация, презентация, отчёты
```

## Что сдавать

- Репозиторий: текущая ссылка GitHub.
- Документация: `AeroMission_Planner_Documentation.pdf` из Drive.
- Презентация: `AeroMission_Planner_Presentation.pdf` / `.pptx` из Drive.
- Прототип: локальный запуск из репозитория или обновлённый `AeroMission_Planner_Repository.zip` из Drive.
- Дополнительные материалы: `AeroMission_Planner_Submission_Pack.zip`.

## Важно

В сдачных материалах нет ссылок на внешние референсные репозитории. Проект оформлен как самостоятельное решение команды **#ЕСТЬТАЛАНТ**.

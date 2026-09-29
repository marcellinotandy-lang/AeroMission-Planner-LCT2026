# Данные для формы сдачи ЛЦТ 2026

Команда: `#ЕСТЬТАЛАНТ`

## Что сдавать в поля формы

- Репозиторий: ссылка на GitHub-репозиторий с содержимым этого архива.
- Документация: можно указать ссылку на `docs/AeroMission_Planner_Documentation.pdf` или на README репозитория.
- Презентация: можно указать ссылку на `docs/AeroMission_Planner_Presentation.pdf` / `.pptx`.
- Прототип: ссылка на репозиторий или на инструкцию запуска в README. Прототип запускается локально через FastAPI и открывается в браузере.
- Дополнительные материалы: `docs/demo_plan_result.json`, `docs/demo_routes.geojson`, `docs/demo_routes.kml`, `docs/llm_judge_review.md`.

## Быстрый push на GitHub

```bash
cd aeromission-planner
git init
git add .
git commit -m "Initial hackathon submission"
git branch -M main
git remote add origin https://github.com/<USER>/<REPO>.git
git push -u origin main
```

Если используешь GitHub CLI:

```bash
gh repo create <USER>/<REPO> --public --source . --remote origin --push
```

## Проверка перед сдачей

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

Открыть: http://localhost:8000

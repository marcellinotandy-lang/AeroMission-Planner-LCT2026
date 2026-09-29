# Frontend Mission Control UI

Финальная версия frontend была переработана в формат operator mission-control:

- левая панель параметров миссии и JSON-сценария;
- центральная карта с рабочей зоной, no-fly полигонами, галсами, стартами, резервными площадками и маршрутами;
- правая панель валидации с makespan, суммарным налетом, числом активных БВС, индексом безопасности и предупреждениями;
- нижний таймлайн флота для проверки распределения работ по каждому борту;
- экспорт рассчитанного плана в GeoJSON/KML.

Актуальная собранная версия frontend находится в обновленном `AeroMission_Planner_Repository.zip` в Google Drive папке сдачи:

https://drive.google.com/drive/folders/1N4fHkZ5UFOO86H7pKiWt5BcRGy-I6NFk

Локальный запуск остается прежним:

```bash
pip install -r requirements.txt
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

После запуска открыть `http://localhost:8000`.

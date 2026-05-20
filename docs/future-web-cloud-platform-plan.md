# CamouFlow documentation

Дата: 2026-05-20

## Что это

CamouFlow сейчас — локальное desktop-приложение для управления браузерными профилями, прокси и сценариями автоматизации.

Основной стек:

- Python
- PyQt6/QML
- Camoufox
- CloakBrowser
- Playwright-style automation core
- локальное хранение данных

## Активный интерфейс

Актуальный UI находится в `app/qml`.

Разделы приложения:

- Dashboard
- Profiles
- Browser
- Proxies
- Scenarios
- Logs
- Settings

Папка `newdesign/` содержит React/Vite-прототип дизайна. Это не основной runtime-интерфейс.

## Dashboard

Dashboard показывает состояние системы:

- количество профилей
- количество запущенных браузеров
- количество сценариев
- количество прокси
- live activity
- running sessions
- быстрые действия для перехода к основным разделам

Скриншот: `images/dashboard.png`.

## Profiles

Раздел Profiles отвечает за браузерные профили.

Возможности:

- создание профилей
- редактирование профиля
- удаление профиля
- запуск профиля
- остановка профиля
- назначение прокси
- управление тегами профилей
- per-profile overrides для браузера

Поля профиля:

- name
- tag/scenario
- proxy host
- proxy port
- proxy user
- proxy password
- locale
- timezone
- user agent
- WebGL/GPU vendor
- CPU cores

Скриншот: `images/profiles.png`.

## Browser

Раздел Browser управляет настройками браузерного движка.

Поддерживаются настройки для:

- Camoufox
- CloakBrowser

Основные группы настроек:

- execution mode
- headless/windowed запуск
- humanization
- OS fingerprint pool
- Cloak fingerprint seed
- locale/timezone
- persistent storage
- viewport/window/screen sizes
- network/rendering restrictions
- navigator overrides
- user agent
- CPU cores
- WebGL/GPU
- addons/fonts/exclude-addons
- extension paths
- launch args

Скриншот: `images/browser.png`.

## Proxies

Раздел Proxies управляет proxy pools.

Возможности:

- создание групп прокси
- переименование групп
- удаление групп
- массовый импорт прокси
- редактирование отдельного прокси
- удаление отдельного прокси
- health-check отдельного прокси
- health-check всей группы
- статистика по active/checking/failed/locations

Поддерживаемые форматы ввода:

```text
socks5://host:port:user:password
http://user:pass@host:port
```

Скриншот: `images/proxies.png`.

## Scenarios

Scenarios — основной редактор автоматизации.

Возможности:

- визуальный node-based canvas
- перемещение шагов
- pan/zoom холста
- success/error связи между шагами
- контекстное меню узлов
- контекстное меню связей
- создание сценария
- дублирование сценария
- удаление сценария
- сохранение сценария
- запуск выбранного сценария на выбранном профиле
- shared variables modal
- редактирование выбранного шага
- preview raw JSON шага

Типы шагов:

- start
- goto
- http_request
- wait_element
- wait_for_load_state
- sleep
- click
- type
- set_var
- parse_var
- pop_shared
- extract_text
- write_file
- compare
- new_tab
- switch_tab
- close_tab
- set_tag
- end
- run_scenario
- log

Shared variables перенесены в раздел Scenarios и открываются через кнопку `Variables` рядом с `Save`.

Скриншот: `images/scenarios.png`.

## Logs

Раздел Logs показывает события приложения и автоматизации.

Возможности:

- просмотр логов
- refresh
- clear

Скриншот: `images/logs.png`.

## Settings

Settings сейчас содержит только базовые настройки приложения.

Текущая функция:

- отображение data root

Shared variables больше не находятся в Settings.

## Локальные данные

CamouFlow хранит локально:

- профили
- прокси
- сценарии
- shared variables
- настройки браузера
- логи
- persistent browser profiles

Data root отображается в Settings.

## Тесты

Текущие тесты:

- `tests/test_dashboard_data.py`
- `tests/test_qml_static.py`

Запуск:

```bat
python -m pytest tests
```

## Сборка

Windows build:

```bat
build.bat
```

Результат:

```text
dist\CamouFlow\CamouFlow.exe
```

## Дальнейшее развитие

Desktop-версия остаётся локальным режимом.

Потенциальное направление развития — отдельная web/cloud-платформа поверх текущего Python-core:

```text
React Web UI
  -> FastAPI Backend
  -> PostgreSQL + Redis
  -> Runner Manager
  -> Docker Runner Nodes
  -> CloakBrowser/Camoufox sessions
```

Что можно переиспользовать:

- browser core
- scenario engine
- step implementations
- profile model
- proxy model
- fingerprint/browser settings

Что нужно проектировать отдельно:

- auth
- teams/workspaces
- API
- cloud runner orchestration
- resource limits
- live browser access
- billing/limits, если продукт станет SaaS

Важно: текущий desktop-код не нужно напрямую превращать в SaaS UI. Правильнее вынести core-логику и строить web-платформу отдельным слоем.

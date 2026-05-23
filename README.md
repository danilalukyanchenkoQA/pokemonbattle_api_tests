pokemonbattle_api_tests/
│
├── 📄 **conftest.py**              # Фикстуры pytest (api_session с токеном)
├── 📄 **pytest.ini**# Настройки pytest (-s -v, pythonpath, markers)
├── 📁 **schemas/**   JSON Schema валидация ответов
│
├── 📁 **config/**
│   └── 📄 **api_config.py**        # BASE_URL = "https://api.pokemonbattle.ru/v2"
│
├── 📁 **data/**
│   └── 📄 **api_constants.py**     | Константы (TRAINER_ID = 50523)
│
├── 📁 **fixtures/**
│   └── 📄 **api_fixtures.py**      | Тестовые данные (JSON payloads)
│
├── 📁 **helpers/** Вспомогательные функции
│
├── 📁 **tests/**
│   └──── 📄 **test_pokemonbattle_api.py**| Главный тестовый файл
│
│
├── 📄 **requirements.txt**         | Зависимости (pytest, requests, ...)
└── 📄 **README.md**               | Документация

🚀 Быстрый старт
bash
# Windows CMD
venv\Scripts\activate
pip install -r requirements.txt
pytest test_pokemonbattle_api.py -s -v

## 🚀 Запуск тестов с Allure отчетами

### 1. Запуск тестов с генерацией данных Allure
```bash
pytest --alluredir=allure-results

Что делает:

Запускает все автотесты проекта
Генерирует сырые данные тестов в папку allure-results/ (JSON/XML файлы)
или
не создает HTML отчет — только исходные данные

2. Генерация и просмотр Allure отчета
bash
allure serve .\allure-results\
allure generate .\allure-results\ - Для генерации HTML отчета, который удобно передавать кому-либо
allure generate allure-results --single-file -o allure-report/complete.html

Что делает:

Читает данные из allure-results/
Генерирует красивый HTML отчет
Автоматически открывает браузер с интерактивным дашбордом
Сервер работает до Ctrl+C
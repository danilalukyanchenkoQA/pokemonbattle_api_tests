import os
import json
from http import HTTPStatus

import allure
import pytest
import requests
from urllib.parse import urlparse, parse_qs

from config.api_config import BASE_URL


@pytest.fixture(scope="session")
def api_session():
    """Requests Session с логированием для Allure"""
    session = requests.Session()
    session.headers.update({"trainer_token": os.getenv("POKEMONBATTLE_TOKEN")})

    def log_request_response(response, method):
        """Логирует request/response (совместимо с PreparedRequest)"""
        # 🌐 URL (парсим params из строки)
        parsed_url = urlparse(response.request.url)
        params = parse_qs(parsed_url.query)
        url_info = f"{method} {response.request.url}"
        if params:
            url_info += f"\nParams: {params}"
        allure.attach(url_info, "🌐 Request URL", allure.attachment_type.TEXT)

        # 📋 Request Headers (без проблем)
        req_headers = dict(response.request.headers)
        allure.attach(
            json.dumps(req_headers, indent=2, ensure_ascii=False),
            "📋 Request Headers",
            allure.attachment_type.JSON
        )

        # 📦 Request Body
        if response.request.body:
            try:
                body_str = response.request.body.decode('utf-8')
                allure.attach(body_str, "📦 Request Body", allure.attachment_type.JSON)
            except:
                allure.attach(str(response.request.body), "📦 Request Body", allure.attachment_type.TEXT)

        # 📊 Response Status
        allure.attach(f"Status: {response.status_code}", "📊 Response Status", allure.attachment_type.TEXT)

        # 📋 Response Headers
        resp_headers = dict(response.headers)
        allure.attach(
            json.dumps(resp_headers, indent=2, ensure_ascii=False),
            "📋 Response Headers",
            allure.attachment_type.JSON
        )

        # 📦 Response Body
        try:
            allure.attach(response.text, "📦 Response Body", allure.attachment_type.JSON)
        except:
            allure.attach(response.text, "📦 Response Body", allure.attachment_type.TEXT)

    # Monkeypatch методов
    methods = ['get', 'post', 'put', 'patch', 'delete']
    original_methods = {}

    for method_name in methods:
        original = getattr(session, method_name)
        original_methods[method_name] = original

        def make_logged_method(original_method=original, m_name=method_name):
            def logged_method(*args, **kwargs):
                response = original_method(*args, **kwargs)
                log_request_response(response, m_name.upper())
                return response

            return logged_method

        setattr(session, method_name, make_logged_method())

    yield session
    session.close()


@pytest.fixture()  # ← Выполняется автоматически для всех тестов в классе
def premium_cleanup(api_session):
    """Очищает Premium после каждого теста"""
    yield  # ← Тест выполняется

    # CANCEL после теста
    cancel_response = api_session.post("https://lavka.pokemonbattle.ru/cancel_premium")

@pytest.fixture()
def prepare_and_clear_battle(api_session):
    response = api_session.get(
        BASE_URL + "/me"
    )
    body = response.json()["data"][0]
    if pokemon_list := body["pokemons_in_pokeballs"]:
        pokemon_id = pokemon_list[0]["id"]
    else:
        if pokemon_list := body.get("pokemons_in_pokeballs"):
            pokemon_id = pokemon_list[0]
        else:
            response = api_session.post(
                        BASE_URL + "/pokemons",
                        json={"name": "generate", "photo_id": -1}
                    )
            body = response.json()
            pokemon_id = body["id"]
        response = api_session.post(
                BASE_URL + "/trainers/add_pokeball",
                json={"pokemon_id": pokemon_id}
        )
        assert response.status_code == HTTPStatus.OK
    yield pokemon_id
    response = api_session.post(
        BASE_URL + "/pokemons/knockout",
        json={"pokemon_id": pokemon_id}
    )

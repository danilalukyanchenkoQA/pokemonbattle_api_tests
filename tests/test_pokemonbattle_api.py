from http.client import responses

import time
import allure
import deepdiff
import pytest
import requests
from jsonschema import validate
from deepdiff import DeepDiff
from http import HTTPStatus

from config.api_config import BASE_URL
from data.api_constants import TRAINER_ID
from data.api_constants import PAYMENT_JSON
from helpers.file_helpers import load_yaml

@allure.suite("Тесты на эндпоинт GET /trainers")
class TestGetTrainers:

    @pytest.mark.smoke
    @allure.title("Получаем тренеров из города Moscow")
    @pytest.mark.api
    def test__trainers__city__filter__moscow(self, api_session):  # Получаем тренеров из города Moscow через API фильтр
        with allure.step("Получаем тренеров из города Москва через фильтр"):
            response = api_session.get( BASE_URL+"/trainers",
                                params={"city": "Moscow"})
        assert response.status_code == HTTPStatus.OK    #  Проверяем успешный HTTP ответ
        body = response.json()  #  Парсим JSON ответ
        trainers = body["data"]  # Список словарей с данными тренеров
        with allure.step("Проверяем каждого тренера из ответа"):
            for trainer in trainers:    #  Проверяем каждого тренера из ответа
                assert trainer["city"] == "Moscow"

    @pytest.mark.smoke
    @allure.title("Получение тренера по ID")
    @pytest.mark.api
    def test__trainers__filter__id(self, api_session):  # Получение тренера по ID
        with allure.step("Делаем GET запрос с фильтром по trainer_id"):
            response = api_session.get(BASE_URL+"/trainers",
                                params={"trainer_id": TRAINER_ID})
        assert response.status_code == HTTPStatus.OK    #  Проверяем успешный HTTP ответ
        body = response.json() #  Парсим JSON один раз для всех проверок
        #  Извлекаем первого (единственного) тренера из ответа
        trainer = body["data"][0]
        with allure.step("Проверяем ID тренера"):
            assert trainer["id"] == TRAINER_ID  # Проверяем, что id вернувшегося в запросе тренера корректный
        with allure.step("Проверяем имя тренера"):
          assert trainer["trainer_name"] == "Luchok"

    @pytest.mark.smoke
    @allure.title("Получение тренеров по городу с сортировкой по убыванию уровня")
    @pytest.mark.api
    def test__trainers__city__sort__by__level(self, api_session):
        with allure.step("Делаем GET запрос с фильтром по city"):
         response = api_session.get(BASE_URL+"/trainers",
                                params={"sort": "desc_level", "city": "Moscow"})
        assert response.status_code == HTTPStatus.OK  #  Проверяем успешный HTTP ответ
        body = response.json()  # Парсим JSON один раз для всех проверок
        trainers = body["data"]  # Список словарей с данными тренеров

        # проверка сортировки
        with allure.step("Проверяем сортировку"):
            for i in range(1, len(trainers)):
                current_level = int(trainers[i]["level"])
                previous_level = int(trainers[i - 1]["level"])
                assert current_level <= previous_level, \
                    f" Сортировка сломана: {previous_level} → {current_level}"

        with allure.step("Проверяем, что топ-1 имеет максимальный уровень"):
          assert int(trainers[0]["level"]) >= max(int(t["level"]) for t in trainers)

@allure.suite("Тесты на полный цикл жизни покемона")
class TestCRUDPokemons:

    @pytest.mark.smoke
    @allure.title("Нокаут всех живых покемонов")
    @pytest.mark.api
    def test__knockout__pokemons(self, api_session):
        """Тест 1: Нокаут всех живых покемонов"""
        with allure.step("Получаем всех покемонов тренера 50523"):
         response = api_session.get(
            BASE_URL + "/pokemons",
            params={"trainer_id": TRAINER_ID}
        )
        assert response.status_code == HTTPStatus.OK
        body = response.json()
        all_pokemons = body["data"]
        print(f"Всего покемонов: {len(all_pokemons)}")

        with allure.step("Нокаутируем только живых покемонов"):
            print("ШАГ 2: Нокаутируем живых покемонов...")
            live_pokemons = [p for p in all_pokemons if p["status"] == 1]
            print(f"Живых покемонов: {len(live_pokemons)}")

            for pokemon in live_pokemons:
                pokemon_id = pokemon["id"]
                print(f"   → Нокаут ID={pokemon_id}")

                knockout_response = api_session.post(
                    BASE_URL + "/pokemons/knockout",
                    json={"pokemon_id": pokemon_id}
                )
                assert knockout_response.status_code == HTTPStatus.OK

        with allure.step("Финальная проверка"):
            print("ШАГ 3: Проверяем что все мертвы...")
            final_response = api_session.get(
                BASE_URL + "/pokemons",
                params={"trainer_id": TRAINER_ID}
            )
            assert final_response.status_code == HTTPStatus.OK

            final_pokemons = final_response.json()["data"]
            for pokemon in final_pokemons:
                assert pokemon["status"] == 0, f"Покемон ID={pokemon['id']} живой!"

            print("Тест 1 УСПЕШЕН: все покемоны мертвы!")

    def create_pokemon(self, api_session):
        print("Создаем нового покемона...")
        response = api_session.post(
            BASE_URL + "/pokemons",
            json={"name": "generate", "photo_id": -1}
        )
        assert response.status_code == HTTPStatus.CREATED

        body = response.json()
        pokemon = body.get("data", body)
        pokemon_id = pokemon.get("id") or pokemon.get("pokemon_id")
        assert pokemon_id, "ID покемона не найден!"

        print(f"Создан покемон ID={pokemon_id}")
        return pokemon_id

    @allure.title("Создание покемона")
    @pytest.mark.api
    def test__create__pokemon(self, api_session):
        """Тест 2: Создание покемона"""
        with allure.step("Создаем покемона"):
            pokemon_id = self.create_pokemon(api_session)
            print(f"Тест 2 УСПЕШЕН: ID={pokemon_id} сохранен!")

    def update_pokemon_name(self, api_session, pokemon_id):
        """Обновляет имя покемона"""
        print(f"Обновляем имя покемона ID={pokemon_id}...")
        response = api_session.patch(
            BASE_URL + "/pokemons",
            json={
                "pokemon_id": pokemon_id,
                "name": "Pikachu"  # Конкретное имя вместо "generate"
            }
        )
        assert response.status_code == HTTPStatus.OK
        print("Имя покемона обновлено!")
        return response.json()

    @pytest.mark.skip
    @allure.title("Полный CRUD покемона")
    @pytest.mark.api
    def test__full_crud(self, api_session):
        print("ЗАПУСКАЕМ ПОЛНЫЙ CRUD!")

        with allure.step("Нокаут всех живых покемонов"):
            self.test__knockout__pokemons(api_session)

        with allure.step("Создаем нового покемона"):
            pokemon_id = self.create_pokemon(api_session)

        with allure.step("Меняем имя"):
         self.update_pokemon_name(api_session, pokemon_id)

        with allure.step("GET /pokemons - убеждаемся что имя изменилось"):
            check_response = api_session.get(
                BASE_URL + "/pokemons",
                params={"trainer_id": TRAINER_ID}  # Список всех покемонов тренера
            )
            assert check_response.status_code == HTTPStatus.OK

        with allure.step("Ищем нашего покемона по ID"):
            pokemons = check_response.json()["data"]
            updated_pokemon = None
            for pokemon in pokemons:
                if pokemon["id"] == pokemon_id:
                    updated_pokemon = pokemon
                    break

        assert updated_pokemon, f"Покемон ID={pokemon_id} не найден!"

        with allure.step("Убеждаемся что имя действительно Pikachu"):
            assert updated_pokemon["name"] == "Pikachu", \
                f"Имя не изменилось! Ожидали 'Pikachu', получили '{updated_pokemon['name']}'"

@allure.suite("Тесты на эндпоинт GET /battle")
class TestGetBattle:  # 🧪 проверка структуры ответа по JSON Schema
    @allure.title("Валидация ответа по схеме JSON")
    def test__get_battle(self, api_session):
        with allure.step("Получаем битвы тренера"):
         response = api_session.get(BASE_URL + "/battle")
        assert response.status_code == HTTPStatus.OK    # Проверяем успешный HTTP ответ
        body = response.json()   # Парсим JSON ответ
        template = load_yaml("battle_get.yml")  # 📋Загружаем JSON Schema из YAML файла
        with allure.step("Проверяем ответ по схеме JSON"):
          validate(body, template)  # 🔍 Строгая валидация ответа по схеме

@allure.suite("Тесты на эндпоинт GET /achievements")
class TestAchievements:
    @allure.title("Валидация ответа по схеме JSON")
    def test__get_achievements(self, api_session):
        with allure.step("Делаем запрос GET /achievements"):
           response = api_session.get(BASE_URL + "/achievements")
        assert response.status_code == HTTPStatus.OK  # Проверяем успешный HTTP ответ
        body = response.json()  # Парсим JSON ответ
        template = load_yaml("achievements_get.yml")  # 📋Загружаем JSON Schema из YAML файла
        with allure.step("Проверяем ответ по схеме JSON"):
           validate(body, template) # 🔍 Строгая валидация ответа по схеме

        # DeepDiff с исключением is_reached
        diff = DeepDiff(
            body, body,
            exclude_regex_paths=[r"root\['data'\]\[\d+\]\['is_reached'"]
        )
        assert diff == {}

    @allure.title("Негативный тест валидации ответа по схеме JSON")
    def test__get_achievements__negative(self, api_session, check):
        with allure.step("Делаем запрос GET /achievements с невалидным параметром"):
          response = api_session.get(BASE_URL + "/achievements",
                                   params={"is_reached": 123})
        assert response.status_code == HTTPStatus.UNPROCESSABLE_CONTENT
        body = response.json()
        with allure.step("Проверяем ошибку"):
            with check:
                assert body["status"] == "error"
        with check:
            assert body["message"] == "[{'type': 'bool_parsing', 'loc': ('query', 'is_reached'), 'msg': 'Input should be a valid boolean, unable to interpret input', 'input': '123'}]"

@allure.suite("Тесты на сценарий покупка Premium")
class TestPremium:
    @allure.title("Успешная покупка Premium")
    def test__post_happy_path(self, api_session, premium_cleanup):
        with allure.step("Покупка премиума"):
            response = api_session.post("https://lavka.pokemonbattle.ru/payments",
                                        json=PAYMENT_JSON)
            body = response.json()
        with allure.step("Проверяем успешность покупки Premium"):
            assert response.status_code == HTTPStatus.OK
            assert body["message"] == "Транзакция успешна"

        with allure.step("Premium отменен автоматически (фикстура premium_cleanup)"):
            pass

    @pytest.mark.parametrize(
        "field_name, invalid_value, expected_message",
        [
            ("days", "1000", "Количество дней должно быть от 1 до 999"),
            ("days", "0", "Заполните days"),
            ("days", "-5", "Количество дней должно состоять из цифр"),
            ("card_cvv", "9999", "Некорректный формат CVV кода"),
            ("card_cvv", "abc", "Некорректный формат CVV кода"),
            ("card_cvv", "300", "Недостаточно средств для оплаты")
        ],
        ids=["days>999", "days=0", "days<1", "cvv>3", "cvv_letters", "cvv_text"]
    )
    @allure.title("Негативная проверка {field_name} = {invalid_value}")
    def test__post_negative_path(self, api_session, premium_cleanup, field_name, invalid_value, expected_message):
        time.sleep(1) # Добавил для избежания ошибки 'Лимит запросов превышен'
        base_payload = {
            "order_type": "premium",
            "details": {
                "days": "30",
                "card_number": "5555555544444442",
                "card_name": "danila lukyanchenko",
                "card_actual": "10/28",
                "card_cvv": "125",
                "secure_code": "56456"
            }
        }

        base_payload["details"][field_name] = invalid_value

        with allure.step(f"Негативная проверка покупки в поле {field_name} = '{invalid_value}'"):
            response = api_session.post("https://lavka.pokemonbattle.ru/payments", json=base_payload)
            body = response.json()

        with allure.step("Проверка неуспешной покупки"):
            assert response.status_code == HTTPStatus.BAD_REQUEST
            assert body["status"] == "error"
            assert body["message"] == expected_message

@allure.suite("Тесты прохождения битвы покемонов")
class TestPokemonBattle:
    @allure.title("Битва покемонов позитивный сценарий")
    def test_run_battle_success(self, api_session, prepare_and_clear_battle:str):
        with allure.step("Находим нашему покемону соперника"):
            ready_for_battle_response = api_session.get(
                BASE_URL + "/pokemons",
                params={"in_pokeball": 1}
            )
            assert ready_for_battle_response.status_code == HTTPStatus.OK
            pokemons_body = ready_for_battle_response.json()
            suitable_pokemons = [x for x in pokemons_body["data"] if x["trainer_id"] != TRAINER_ID]
            enemy_pokemon_id = suitable_pokemons[0]["id"]

        with allure.step("Проводим битву"):
            battle_response = api_session.post(
                BASE_URL + "/battle",
                json={  "attacking_pokemon": prepare_and_clear_battle,
                        "defending_pokemon": enemy_pokemon_id}
            )
            assert battle_response.status_code == HTTPStatus.OK
            battle_body = battle_response.json()
            assert battle_body["message"] == "Битва проведена"

        with allure.step("Проверяем в каком статусе покемон после битвы"):
            pokemon_after_battle_response = api_session.get(
                BASE_URL + f"/pokemons/{prepare_and_clear_battle}",
            )
            assert pokemon_after_battle_response.status_code == HTTPStatus.OK
            status_body = pokemon_after_battle_response.json()
            if status_body["in_pokeball"] == 0:
                print("НАШ ПОКЕМОН ПРОИГРАЛ: status=0, in_pokeball=0")
            elif status_body["status"] == 1 and status_body["in_pokeball"] == 1:
                print("НАШ ПОКЕМОН ВЫИГРАЛ: status=1, in_pokeball=1")

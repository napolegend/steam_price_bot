import requests
import logging

def get_game_info(game_id: int):
    url = f"https://store.steampowered.com/api/appdetails?appids={game_id}"
    try:
        response = requests.get(url, timeout=35)
        data = response.json()
        game_data = data.get(str(game_id), {}).get("data")

        if not game_data:
            return None

        # Проверка на бесплатную игру
        if game_data.get("is_free", True):
            return {
                "name": game_data.get("name"),
                "price": 0.0,
                "is_free": True
            }

        # Проверка наличия ценовой информации
        if "price_overview" not in game_data:
            return {
                "name": game_data.get("name"),
                "price": None,
                "is_free": False
            }

        return {
            "name": game_data.get("name"),
            "price": game_data["price_overview"]["final"] / 100,
            "is_free": False
        }
    except Exception as e:
        logging.error(f"Steam API error: {e}")
        return None
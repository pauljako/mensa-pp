import re
import sys
import urllib.parse

import bs4
import requests

URL = "https://mutlangen.mensa-pro.de/index.php"
HEADERS = {"User-Agent": "Mozilla/5.0"}


def login(user_id, password) -> tuple[str | None, str | None]:
    """Logs the User in and returns a session id"""
    response = requests.post(
        URL,
        headers=HEADERS,
        data={"user_id": user_id, "user_pwd": password},
    )
    valid = (bs4.BeautifulSoup(response.text, "html.parser").find(string=re.compile("Login inkorrekt")) is None)
    if not valid:
        return None, None

    name = bs4.BeautifulSoup(response.text, "html.parser").find_all(class_="nav_act")[1].get_text()

    cookies = requests.utils.dict_from_cookiejar(response.cookies)
    if "PHPSESSID" in cookies:
        return cookies["PHPSESSID"], name

    return None, name


def get_menu(session_id: str, timestamp: str | None) -> dict[int, list[dict[str, str]]] | None:
    """Returns the food menu"""
    if timestamp is None:
        params = {}
    else:
        params = {"ts": timestamp}

    response = requests.get(URL, headers=HEADERS, cookies={"PHPSESSID": session_id}, params=params)
    soup = bs4.BeautifulSoup(response.text, "html.parser")
    results = soup.find_all("table", class_="essensplan_cont")

    meals = {0: []}
    current_menu = 0

    for table in results:

        rows = table.find_all("tr")

        if len(rows) != 2:
            continue

        if len(meals[current_menu]) >= 5:
            current_menu += 1
            meals[current_menu] = []

        td = rows[0].find("td", colspan="2")
        if not td:
            continue

        link = rows[1].find("a", href=True)

        state = "unavailable"
        meal_id = None

        if link:
            state_text = link.get_text(strip=True)
            match state_text:
                case "bestellen":
                    state = "available"
                case "bestellt":
                    state = "ordered_past"
                case "storno":
                    state = "ordered"
                case _:
                    state = "unavailable"

            query = urllib.parse.urlparse(link["href"]).query
            params = urllib.parse.parse_qs(query)
            if "essenid" in params:
                meal_id = params.get("essenid", [None])[0]
            elif "storno" in params:
                meal_id = params.get("storno", [None])[0]
            else:
                meal_id = None

        if td.find("i") and "Kein Essen verfügbar" in td.get_text():
            meals[current_menu].append(None)
        else:

            price_td = rows[1].find("td")
            price = price_td.get_text(strip=True) if price_td else None

            meal_text = " ".join(td.stripped_strings)
            meal_text = " ".join(meal_text.split())
            meal_item = {"name": meal_text.split(" | "), "price": price, "state": state, "meal_id": meal_id}
            meals[current_menu].append(meal_item)

    return meals


def order_meal(session_id: str, meal_id: str) -> bool:
    """Orders an Item from the menu"""
    response = requests.get(URL, headers=HEADERS, cookies={"PHPSESSID": session_id},
                            params={"essenid": meal_id, "bestellvorgang": "true"})

    return response.ok


def cancel_meal(session_id: str, meal_id: str) -> bool:
    """Cancels an ordered Meal from the menu"""
    response = requests.get(URL, headers=HEADERS, cookies={"PHPSESSID": session_id}, params={"storno": meal_id})

    return response.ok


if __name__ == "__main__":
    session_id = login(input("Enter User-ID: "), input("Enter Password: "))
    if session_id is None:
        sys.exit(1)

    menu = get_menu(session_id, None)
    print(menu)

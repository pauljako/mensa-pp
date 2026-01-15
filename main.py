import flask
import flask_cors

import scraper

app = flask.Flask(__name__)
flask_cors.CORS(app)


@app.route("/api/login", methods=["POST"])
def login():
    if "id" not in flask.request.form or "password" not in flask.request.form:
        return "id and password expected in form", 400

    session_id = scraper.login(flask.request.form["id"], flask.request.form["password"])

    if session_id is None:
        return "Wrong credentials", 401
    else:
        return {"session_id": session_id}, 200


@app.route("/api/menu", methods=["GET"])
def get_menu():
    if "Session-Id" not in flask.request.headers:
        return "Authentication expected", 401

    session_id = flask.request.headers.get("Session-Id")

    if "Timestamp" in flask.request.headers:
        timestamp = flask.request.headers["Timestamp"]
    else:
        timestamp = None

    menu = scraper.get_menu(session_id, timestamp)

    if menu is None:
        return "Failed to get menu", 500
    else:
        return menu, 200


@app.route("/api/order", methods=["POST"])
def order():
    if "Session-Id" not in flask.request.headers:
        return "Authentication expected", 401

    session_id = flask.request.headers.get("Session-Id")

    if "Meal-Id" not in flask.request.headers:
        return "Meal-Id expected", 400
    else:
        meal_id = flask.request.headers["Meal-Id"]

    result = scraper.order_meal(session_id, meal_id)

    if result:
        return "success", 200
    else:
        return "error", 500


@app.route("/api/cancel", methods=["DELETE"])
def cancel():
    if "Session-Id" not in flask.request.headers:
        return "Authentication expected", 401

    session_id = flask.request.headers.get("Session-Id")

    if "Meal-Id" not in flask.request.headers:
        return "Meal-Id expected", 400
    else:
        meal_id = flask.request.headers["Meal-Id"]

    result = scraper.cancel_meal(session_id, meal_id)

    if result:
        return "success", 200
    else:
        return "error", 500


if __name__ == "__main__":
    app.run("0.0.0.0", 32339)

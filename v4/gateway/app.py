from flask import Flask, jsonify, request
import requests

app = Flask(__name__)

# В Docker-сети имена контейнеров = hostnames
LIBRARY_URL = "http://library_service:8060"
RATING_URL = "http://rating_service:8050"
RESERVATION_URL = "http://reservation_service:8070"

# Пример: получить список всех библиотек
@app.route("/api/v1/libraries", methods=["GET"])
def get_libraries():
    resp = requests.get(f"{LIBRARY_URL}/libraries")
    return jsonify(resp.json()), resp.status_code

# Пример: получить рейтинг книги
@app.route("/api/v1/books/<book_uid>/rating", methods=["GET"])
def get_book_rating(book_uid):
    resp = requests.get(f"{RATING_URL}/ratings/{book_uid}")
    return jsonify(resp.json()), resp.status_code

# Пример: создать бронирование книги
@app.route("/api/v1/reservations", methods=["POST"])
def create_reservation():
    data = request.get_json()
    resp = requests.post(f"{RESERVATION_URL}/reservations", json=data)
    return jsonify(resp.json()), resp.status_code

# Пример: получить все бронирования пользователя
@app.route("/api/v1/reservations", methods=["GET"])
def get_reservations():
    user_id = request.args.get("user_id")
    resp = requests.get(f"{RESERVATION_URL}/reservations?user_id={user_id}")
    return jsonify(resp.json()), resp.status_code

# Health check
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

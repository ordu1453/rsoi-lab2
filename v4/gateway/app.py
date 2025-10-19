from flask import Flask, jsonify, request
import requests

app = Flask(__name__)

LIBRARY_URL = "http://library_service:8060"
RATING_URL = "http://rating_service:8050"
RESERVATION_URL = "http://reservation_service:8070"

@app.route("/api/v1/libraries", methods=["GET"])
def get_libraries():
    city = request.args.get('city')
    category = request.args.get("category")
    page = request.args.get("page")

    params = {
        "category": category,
        "page": page,
        "city": city
    }

    response = requests.get(f"{LIBRARY_URL}/libraries", params=params, timeout=5)
    if response.status_code == 200:
        try:
            data = response.json()
            print(data)
        except ValueError:
            print("Ответ не в формате JSON:", response.text)
    else:
        print(f"Ошибка {response.status_code}: {response.text}")
    return jsonify(response.json()), response.status_code

@app.route('/api/v1/libraries/<library_uid>/books', methods=['GET'])
def get_books(library_uid):
    category = request.args.get("category")
    page = request.args.get("page")

    params = {
        "category": category,
        "page": page
    }

    response = requests.get(f"{LIBRARY_URL}/libraries/{library_uid}/books", params=params, timeout=5)
    if response.status_code == 200:
        try:
            data = response.json()
            print(data)
        except ValueError:
            print("Ответ не в формате JSON:", response.text)
    else:
        print(f"Ошибка {response.status_code}: {response.text}")
    return jsonify(response.json()), response.status_code


@app.route("/api/v1/books/<book_uid>/rating", methods=["GET"])
def get_book_rating(book_uid):
    resp = requests.get(f"{RATING_URL}/ratings/{book_uid}")
    return jsonify(resp.json()), resp.status_code

@app.route("/api/v1/reservations", methods=["POST"])
def create_reservation():
    content_type = request.headers.get("Content-Type")
    user_name = request.headers.get("X-User-Name")

    if not user_name:
        return jsonify({"message": "Header X-User-Name is required"}), 400

    data = request.get_json()
    book_uid = data.get("bookUid")
    library_uid = data.get("libraryUid")
    till_date = data.get("tillDate")

    if not all([book_uid, library_uid, till_date]):
        return jsonify({"message": "bookUid, libraryUid and tillDate are required"}), 400

    # --- Проверяем количество арендованных книг ---
    rented_resp = requests.get(f"{RESERVATION_URL}/reservations/{user_name}/count")
    rented_count = rented_resp.json().get("rentedCount", 0) if rented_resp.status_code == 200 else 0

    # --- Получаем рейтинг пользователя ---
    rating_resp = requests.get(f"{RATING_URL}/rating", headers={"X-User-Name": user_name})
    stars = rating_resp.json().get("stars", 0) if rating_resp.status_code == 200 else 0

    # --- Проверяем лимит ---
    max_books_allowed = stars
    if rented_count >= max_books_allowed:
        return jsonify({"message": "Maximum number of rented books reached"}), 400


    # --- Получаем информацию о библиотеке ---
    lib_resp = requests.get(f"{LIBRARY_URL}/libraries/{library_uid}")
    library_data = lib_resp.json() if lib_resp.status_code == 200 else {}

    # --- Получаем информацию о книге ---
    book_resp = requests.get(f"{LIBRARY_URL}/libraries/{library_uid}/{book_uid}")
    book_data = book_resp.json() if book_resp.status_code == 200 else {}
  
    # --- Создаём запись в Reservation Service ---
    payload = {
        "bookUid": book_uid,
        "libraryUid": library_uid,
        "tillDate": till_date
    }
    headers = {"Content-Type": content_type, "X-User-Name": user_name}
    reservation_resp = requests.post(f"{RESERVATION_URL}/reservations", json=payload, headers=headers)

    if reservation_resp.status_code not in (200, 201):
        return jsonify({"message": "Failed to create reservation"}), reservation_resp.status_code

    reservation_json = reservation_resp.json()

    # --- Уменьшаем количество доступных книг ---
    requests.patch(f"{LIBRARY_URL}/api/v1/books/{book_uid}/decrement", json={"libraryUid": library_uid})

    # --- Финальный JSON ---
    resp = {
        "reservationUid": reservation_json.get("reservationUid"),
        "status": reservation_json.get("status", "RENTED"),
        "startDate": reservation_json.get("startDate"),
        "tillDate": till_date,
        "book": {
            "bookUid": book_uid,
            "name": book_data.get("name", ""),
            "author": book_data.get("author", ""),
            "genre": book_data.get("genre", "")
        },
        "library": {
            "libraryUid": library_uid,
            "name": library_data.get("name", ""),
            "address": library_data.get("address", ""),
            "city": library_data.get("city", "")
        },
        "rating": {
            "stars": stars
        }
    }

    return jsonify(resp), 200



@app.route("/api/v1/reservations", methods=["GET"])
def get_reservations():
    user_id = request.args.get("user_id")
    resp = requests.get(f"{RESERVATION_URL}/reservations?user_id={user_id}")
    return jsonify(resp.json()), resp.status_code

@app.route('/api/v1/reservations/<reservation_uid>/return', methods=['POST'])
def return_book(reservation_uid):
    user_name = request.headers.get("X-User-Name")
    data = request.get_json()

    condition = data.get("condition")
    date = data.get("date")

    headers = {
        "X-User-Name":user_name
    }

    json = {
        "condition":condition,
        "date": date
    }
    resp = requests.post(f"{RESERVATION_URL}/reservations/{reservation_uid}/return", json=json, headers=headers)
    return jsonify(resp.json()), resp.status_code

@app.route("/api/v1/rating", methods = ["GET"])
def get_rating():
    user_name = request.headers.get("X-User-Name")
    headers = {"X-User-Name" : user_name}
    resp = requests.get(f"{RATING_URL}/rating", headers=headers, timeout=5)
    return jsonify(resp.json()), resp.status_code

@app.route('/manage/health', methods=['GET'])
def health():
    return "OK", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

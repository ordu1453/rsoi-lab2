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
    data = request.get_json()

    book_uid = data.get("bookUid")
    library_uid = data.get("libraryUid")
    till_date = data.get("tillDate")

    headers = {"Content-Type" : content_type,
               "X-User-Name": user_name}
    json = {"bookUid":book_uid, 
            "libraryUid": library_uid,
            "tillDate":till_date}
    data = request.get_json()
    resp = requests.post(f"{RESERVATION_URL}/reservations", json=json, headers=headers)
    return jsonify(resp.json()), resp.status_code

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

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from uuid import uuid4
import os

app = Flask(__name__)

# Используем имя сервиса 'postgres' вместо 'localhost'
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://program:test@postgres:5432/libraries"
)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
db = SQLAlchemy(app)


# Модели
class Library(db.Model):
    __tablename__ = 'library'
    id = db.Column(db.Integer, primary_key=True)
    library_uid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid4()))
    name = db.Column(db.String(80), nullable=False)
    city = db.Column(db.String(255), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    books = relationship('LibraryBook', back_populates='library')


class Book(db.Model):
    __tablename__ = 'books'
    id = db.Column(db.Integer, primary_key=True)
    book_uid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid4()))
    name = db.Column(db.String(255), nullable=False)
    author = db.Column(db.String(255))
    genre = db.Column(db.String(255))
    condition = db.Column(db.String(20), default='EXCELLENT')  # EXCELLENT, GOOD, BAD
    libraries = relationship('LibraryBook', back_populates='book')


class LibraryBook(db.Model):
    __tablename__ = 'library_books'
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), primary_key=True)
    library_id = db.Column(db.Integer, db.ForeignKey('library.id'), primary_key=True)
    available_count = db.Column(db.Integer, nullable=False)
    book = relationship('Book', back_populates='libraries')
    library = relationship('Library', back_populates='books')


# Инициализация базы (для теста)
@app.before_request
def create_tables():
    db.create_all()



    # Проверяем, есть ли данные, чтобы не дублировать
    if not Library.query.first():
        # Создаем библиотеку
        library = Library(
            id=1,
            library_uid="83575e12-7ce0-48ee-9931-51919ff3c9ee",
            name="Библиотека имени 7 Непьющих",
            city="Москва",
            address="2-я Бауманская ул., д.5, стр.1"
        )
        db.session.add(library)

        # Создаем книгу
        book = Book(
            id=1,
            book_uid="f7cdc58f-2caf-4b15-9727-f89dcc629b27",
            name="Краткий курс C++ в 7 томах",
            author="Бьерн Страуструп",
            genre="Научная фантастика",
            condition="EXCELLENT"
        )
        db.session.add(book)

        # Связываем книгу с библиотекой
        lib_book = LibraryBook(
            book_id=book.id,
            library_id=library.id,
            available_count=1
        )
        db.session.add(lib_book)

        db.session.commit()
        print("Test data created")


# Эндпоинт для списка библиотек
@app.route('/api/v1/libraries', methods=['GET'])
def get_libraries():
    city = request.args.get('city')
    page = int(request.args.get('page', 1))
    size = int(request.args.get('size', 10))
    if not city:
        return jsonify({"message": "City parameter is required"}), 400

    query = Library.query.filter_by(city=city)
    total = query.count()
    libraries = query.offset((page-1)*size).limit(size).all()
    items = [
        {
            "libraryUid": lib.library_uid,
            "name": lib.name,
            "address": lib.address,
            "city": lib.city
        } for lib in libraries
    ]
    return jsonify({
        "page": page,
        "pageSize": size,
        "totalElements": total,
        "items": items
    })


# Эндпоинт для списка книг в библиотеке
@app.route('/api/v1/libraries/<library_uid>/books', methods=['GET'])
def get_books(library_uid):
    show_all = request.args.get('showAll', 'false').lower() == 'true'
    page = int(request.args.get('page', 1))
    size = int(request.args.get('size', 10))

    library = Library.query.filter_by(library_uid=library_uid).first()
    if not library:
        return jsonify({"message": "Library not found"}), 404

    query = LibraryBook.query.filter_by(library_id=library.id)
    if not show_all:
        query = query.filter(LibraryBook.available_count > 0)

    total = query.count()
    library_books = query.offset((page-1)*size).limit(size).all()
    items = [
        {
            "bookUid": lb.book.book_uid,
            "name": lb.book.name,
            "author": lb.book.author,
            "genre": lb.book.genre,
            "condition": lb.book.condition,
            "availableCount": lb.available_count
        } for lb in library_books
    ]
    return jsonify({
        "page": page,
        "pageSize": size,
        "totalElements": total,
        "items": items
    })


# Health check
@app.route('/manage/health', methods=['GET'])
def health():
    return "OK", 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8060, debug=True)

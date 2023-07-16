from quopri import decodestring
from sqlite3 import connect

from patterns.behavioral_patterns import Subject, FileWriter, ConsoleWriter
from patterns.architectural_patterns import DomainObject

connection = connect('theRise.sqlite')


class User:
    auto_id = 0

    def __init__(self, first_name, last_name):
        self.id = self.auto_id
        User.auto_id += 1
        self.first_name = first_name
        self.last_name = last_name


class Author(User):
    pass


class Reader(User, DomainObject):
    def __init__(self, first_name, last_name):
        self.books = []
        super().__init__(first_name, last_name)


# паттерн фабрика
class UserFactory:
    types = {
        'author': Author,
        'reader': Reader,
    }

    @classmethod
    def create(cls, type_, first_name, last_name):
        return cls.types[type_](first_name, last_name)


class Category:
    auto_id = 0

    def __init__(self, name):
        self.id = self.auto_id
        Category.auto_id += 1
        self.name = name
        self.books = []


class Book(Subject, DomainObject):

    def __init__(self, name, author, category):
        self.name = name
        self.author = f'{author.first_name} {author.last_name}' if author.last_name else f'{author.first_name}'
        self.category = category.name
        category.books.append(self)
        self.readers = []
        super().__init__()

    def __getitem__(self, item):
        return self.readers[item]

    def add_reader(self, reader):
        self.readers.append(reader)
        print(self.readers)
        reader.books.append(self)
        print(reader.books)
        self.notify()


class ScientificBook(Book):
    pass


class StudyBook(Book):
    pass


class ReferenceBook(Book):
    pass


# паттерн фабрика
class BookFactory:
    types = {
        'study': StudyBook,
        'reference': ReferenceBook,
        'scientific': ScientificBook,
    }

    @classmethod
    def create(cls, type_, name, author, category):
        return cls.types[type_](name, author, category)


class Engine:

    def __init__(self):
        self.books = []
        self.authors = []
        self.readers = []
        self.categories = []

    @staticmethod
    def create_user(type_, first_name=None, last_name=None):
        return UserFactory.create(type_, first_name, last_name)

    @staticmethod
    def create_category(name):
        return Category(name)

    @staticmethod
    def create_book(type_, name, author, category):
        return BookFactory.create(type_, name, author, category)

    def get_book(self, book_name):
        for book in self.books:
            if book.name == book_name:
                return book
        raise Exception(f'Книга не найдена!')

    def get_category_by_id(self, cat_id):
        for item in self.categories:
            if item.id == cat_id:
                return item
        raise Exception(f'Категории с id = {cat_id} не найдены!')

    def get_reader_by_id(self, user_id):
        for user in self.readers:
            if user.id == user_id:
                return user
        raise Exception(f'Пользователь с id = {user_id} не найден!')

    @staticmethod
    def decode_value(val):
        val_b = bytes(val.replace('%', '=').replace("+", " "), 'UTF-8')
        val_decode_str = decodestring(val_b)
        return val_decode_str.decode('UTF-8')


# порождающий паттерн Синглтон
class Singleton(type):

    def __init__(cls, name, bases, attrs, **kwargs):
        super().__init__(name, bases, attrs)
        cls.__instance = {}

    def __call__(cls, *args, **kwargs):
        if args:
            name = args[0]
        if kwargs:
            name = kwargs['name']

        if name in cls.__instance:
            return cls.__instance[name]
        else:
            cls.__instance[name] = super().__call__(*args, **kwargs)
            return cls.__instance[name]


class Logger(metaclass=Singleton):

    def __init__(self, name, writer=ConsoleWriter()):
        self.name = name
        self.writer = writer

    def log(self, text):
        text = f'LOG >>> {text}'
        self.writer.write(text)


# маппер для читателей
class ReaderMapper:

    def __init__(self, connection):
        self.connection = connection
        self.cursor = connection.cursor()
        self.table_name = 'reader'

    def all(self):
        statement = f'SELECT * from {self.table_name}'
        self.cursor.execute(statement)

        result = []

        for item in self.cursor.fetchall():
            id, name, surname = item
            reader = Reader(name, surname)
            reader.id = id
            result.append(reader)

        return result

    def find_by_id(self, id):
        statement = f"SELECT id, first_name, last_name FROM {self.table_name} WHERE id=?"
        self.cursor.execute(statement, (id,))
        result = self.cursor.fetchone()

        if result:
            return Reader(*result)
        else:
            raise RecordNotFoundException(f'record with id={id} not found')

    def insert(self, obj):
        statement = f"INSERT INTO {self.table_name} (first_name, last_name) VALUES (?, ?)"
        self.cursor.execute(statement, (obj.first_name, obj.last_name))
        try:
            self.connection.commit()
        except Exception as e:
            raise DbCommitException(e.args)

    def update(self, obj):
        statement = f"UPDATE {self.table_name} SET first_name=?, last_name=? WHERE id=?"

        self.cursor.execute(statement, (obj.first_name, obj.last_name, obj.id))
        try:
            self.connection.commit()
        except Exception as e:
            raise DbUpdateException(e.args)

    def delete(self, obj):
        statement = f"DELETE FROM {self.table_name} WHERE id=?"
        self.cursor.execute(statement, (obj.id,))
        try:
            self.connection.commit()
        except Exception as e:
            raise DbDeleteException(e.args)


# маппер для книг
class BookMapper:

    def __init__(self, connection):
        self.connection = connection
        self.cursor = connection.cursor()
        self.table_name = 'book'

    def all(self):
        statement = f'SELECT * from {self.table_name}'
        self.cursor.execute(statement)

        result = []

        for item in self.cursor.fetchall():
            id, name, author, category = item
            author = Author(author.split()[0], author.split()[1]) if len(author.split()) >= 2 else \
                Author(author.split()[0], '')
            category = Category(category)
            book = Book(name, author, category)
            result.append(book)

        return result

    def find_by_name(self, name):
        statement = f"SELECT id, name, author, category FROM {self.table_name} WHERE name=?"
        self.cursor.execute(statement, (name,))
        result = self.cursor.fetchone()

        if result:
            return Book(*result)
        else:
            raise RecordNotFoundException(f'record with name={name} not found')

    def insert(self, obj):
        statement = f"INSERT INTO {self.table_name} (name, author, category) VALUES (?, ?, ?)"
        self.cursor.execute(statement, (obj.name, obj.author, obj.category))
        try:
            self.connection.commit()
        except Exception as e:
            raise DbCommitException(e.args)

    def update(self, obj):
        statement = f"UPDATE {self.table_name} SET name=?, author=? category=? WHERE name=?"

        self.cursor.execute(statement, (obj.name, obj.author, obj.category, obj.name))
        try:
            self.connection.commit()
        except Exception as e:
            raise DbUpdateException(e.args)

    def delete(self, obj):
        statement = f"DELETE FROM {self.table_name} WHERE name=?"
        self.cursor.execute(statement, (obj.name,))
        try:
            self.connection.commit()
        except Exception as e:
            raise DbDeleteException(e.args)


# паттерн - Data Mapper
class MapperRegistry:
    mappers = {
        'reader': ReaderMapper,
        'book': BookMapper,
    }

    @staticmethod
    def get_mapper(obj):
        if isinstance(obj, Reader):
            return ReaderMapper(connection)
        elif isinstance(obj, Book):
            return BookMapper(connection)

    @staticmethod
    def get_current_mapper(name):
        return MapperRegistry.mappers[name](connection)


# классы исключения
class DbCommitException(Exception):
    def __init__(self, message):
        super().__init__(f'Db commit error: {message}')


class DbUpdateException(Exception):
    def __init__(self, message):
        super().__init__(f'Db update error: {message}')


class DbDeleteException(Exception):
    def __init__(self, message):
        super().__init__(f'Db delete error: {message}')


class RecordNotFoundException(Exception):
    def __init__(self, message):
        super().__init__(f'Record not found: {message}')

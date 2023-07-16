from patterns.behavioral_patterns import Serializer
from theRise_framework.templator import render
from patterns.creational_patterns import Engine, Logger, MapperRegistry
from theRise_framework.utils.pre_filling_page import index_filling
from theRise_framework.utils.validators import name_validator
from patterns.structural_patterns import AppRoute, Debug
from patterns.behavioral_patterns import EmailNotifier, SmsNotifier, TemplateView, ListView, CreateView
from patterns.architectural_patterns import UnitOfWork

website = Engine()
logger = Logger('mainLogger')
email_notifier = EmailNotifier()
sms_notifier = SmsNotifier()
UnitOfWork.new_current()
UnitOfWork.get_current().set_mapper_registry(MapperRegistry)

routes = {}


@AppRoute(routes, url='/')
class Index:
    @Debug('index')
    def __call__(self, request):
        # наполнение сайта данными
        index_filling(website)

        return '200 OK', render('index.html',
                                date=request.get('date', None), title=request.get('title'),
                                categories=website.categories)


@AppRoute(routes, url='/contacts/')
class Contacts:
    @Debug('contacts')
    def __call__(self, request):
        return '200 OK', render('contacts.html', title=request.get('title'),
                                categories=website.categories)


@AppRoute(routes, url='/books/')
class Books:
    @Debug('book_list')
    def __call__(self, request):
        logger.log('Book list')
        try:
            category = website.get_category_by_id(int(request['request_params']['id']))
            logger.log(category.books)
            return '200 OK', render('books.html', title=request.get('title'),
                                    objects_list=category.books, categories=website.categories)

        except KeyError:
            logger.log(website.books)
            mapper = MapperRegistry.get_current_mapper('book').all()
            return '200 OK', render('books.html', title=request.get('title'),
                                    objects_list=mapper, categories=website.categories)


@AppRoute(routes, url='/create_book/')
class CreateBook:
    @Debug('create_book')
    def __call__(self, request):
        if request['method'] == 'POST':
            data = request['data']

            # название книги
            name = data['name']
            name = website.decode_value(name)

            # автор книги
            author = data['author']
            author = website.decode_value(author)
            author, length = name_validator(author)
            website.authors.append(website.create_user('author', author[0], author[1])) if length == 2 \
                else website.authors.append(website.create_user('author', author[0]))

            # категория
            category_id = data['category']
            category = website.get_category_by_id(int(category_id))

            book = website.create_book('study', name, website.authors[-1], category)

            book.observers.append(email_notifier)
            book.observers.append(sms_notifier)

            website.books.append(book)
            book.mark_new()
            UnitOfWork.get_current().commit()

            logger.log('Book has been successfully added')

            return '200 OK', render('books.html', title=request.get('title'),
                                    objects_list=website.books, categories=website.categories)

        else:
            if website.categories:
                return '200 OK', render('create_book.html', title=request.get('title'),
                                        categories=website.categories)
            else:
                return '200 OK', 'No categories have been added yet'


@AppRoute(routes, url='/create_category/')
class CreateCategory:
    @Debug('create_category')
    def __call__(self, request):
        logger.log('Category list')

        if request['method'] == 'POST':
            data = request['data']

            name = data['name']
            name = website.decode_value(name)

            category = website.create_category(name)
            website.categories.append(category)

            logger.log(website.categories)
            return '200 OK', render('create_category.html', title=request.get('title'),
                                    categories=website.categories)
        else:
            logger.log(website.categories)
            return '200 OK', render('create_category.html', title=request.get('title'),
                                    categories=website.categories)


@AppRoute(routes=routes, url='/api/')
class BookApi:
    @Debug(name='BookApi')
    def __call__(self, request):
        return '200 OK', Serializer(website.books).save()


@AppRoute(routes=routes, url='/readers/')
class ReadersListView(ListView):
    queryset = website.readers
    template_name = 'readers.html'

    def get_queryset(self):
        mapper = MapperRegistry.get_current_mapper('reader')
        return mapper.all()


@AppRoute(routes=routes, url='/create_user/')
class StudentCreateView(CreateView):
    template_name = 'create_user.html'

    def create_obj(self, data):
        name = data['name']
        surname = data['surname']
        category = data['category']

        name = website.decode_value(name)
        surname = website.decode_value(surname)
        category = website.decode_value(category)

        user = website.create_user(category, name, surname)
        if category == 'author':
            website.authors.append(user)
        elif category == 'reader':
            website.readers.append(user)
            user.mark_new()
            UnitOfWork.get_current().commit()


@AppRoute(routes=routes, url='/read_book/')
class AddStudentByCourseCreateView(CreateView):
    template_name = 'read_book.html'

    def get_context_data(self):
        context = super().get_context_data()
        context['books'] = website.books
        context['readers'] = website.readers
        return context

    def create_obj(self, data: dict):
        book = data['book_name']
        book = website.decode_value(book)
        book = website.get_book(book)

        reader_id = data['reader_id']
        reader = website.get_reader_by_id(int(reader_id))

        book.add_reader(reader)

def fill_data(engine, create_data: str, **kwargs):
    types = {
        'category': (engine.categories, engine.create_category),
        'book': (engine.books, engine.create_book),
        'author': (engine.authors, engine.create_user),
        'reader': (engine.readers, engine.create_user),
    }

    types[create_data][0].append(types[create_data][1](**kwargs))


def index_filling(engine):
    if not engine.categories:
        fill_data(engine, 'category', name='Scientific literature')
        fill_data(engine, 'category', name='Reference books')
        fill_data(engine, 'category', name='Educational literature')
        # fill_data(engine, 'author', type_='author', first_name='Адитья', last_name='Бхаргава')
        # fill_data(engine, 'author', type_='author', first_name='Владимир', last_name='Дронов')
        # fill_data(engine, 'author', type_='author', first_name='Jake', last_name='VanderPlas')
        # fill_data(engine, 'reader', type_='reader', first_name='Yard', last_name='Meski')
        # fill_data(engine, 'reader', type_='reader', first_name='Frank', last_name='Palace')
        # fill_data(engine, 'book', type_='study', name='Грокаем алгоритмы',
        #           author=engine.authors[0], category=engine.categories[2])
        # fill_data(engine, 'book', type_='reference', name='Практика создания веб-сайтов на Python',
        #           author=engine.authors[1], category=engine.categories[1])
        # fill_data(engine, 'book', type_='scientific', name='Python для сложных задач',
        #           author=engine.authors[2], category=engine.categories[0])

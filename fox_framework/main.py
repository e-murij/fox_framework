from os import path
from quopri import decodestring

from components.content_types import CONTENT_TYPES_MAP
from fox_framework.request_framework import GetRequests, PostRequests


class PageNotFound404:
    def __call__(self, request):
        return '404 WHAT', '404 PAGE Not Found'


class Framework:

    """Класс Framework - основа фреймворка"""

    def __init__(self, routes_obj, fronts_obj, settings):
        self.routes_lst = routes_obj
        self.settings = settings
        self.fronts_lst = fronts_obj

    def __call__(self, environ, start_response):
        request = {}
        # наполняем словарь request элементами
        # этот словарь получат все контроллеры
        # отработка паттерна front controller
        for front in self.fronts_lst:
            front(request)

        # получаем адрес, по которому выполнен переход
        path = environ['PATH_INFO']

        # Получаем метод запроса
        method = environ['REQUEST_METHOD']
        request['method'] = method

        # Получаем все данные запроса
        if method == 'POST':
            data = PostRequests().get_request_params(environ)
            request['data'] = Framework.decode_value(data)
            print(f"Post-запрос: {request['data'] }")
        if method == 'GET':
            # 127.0.0.1:8080?id=1&category=10
            request_params = GetRequests().get_request_params(environ)
            request['request_params'] = Framework.decode_value(request_params)
            print(f"GET-запрос с параметрами: {request['request_params'] }")

        # добавление закрывающего слеша
        if not path.endswith('/'):
            path = f'{path}/'

        # находим нужный контроллер
        # отработка паттерна page controller
        if path in self.routes_lst:
            view = self.routes_lst[path]
            content_type = self.get_content_type(path)
            code, body = view(request)
            body = body.encode('utf-8')

        elif path.startswith(self.settings.STATIC_URL):
            file_path = path[len(self.settings.STATIC_URL):len(path)-1]
            content_type = self.get_content_type(file_path)
            code, body = self.get_static(self.settings.STATIC_FILES_DIR, file_path)

        else:
            view = PageNotFound404()
            content_type = self.get_content_type(path)
            code, body = view(request)
            body = body.encode('utf-8')

        # запуск контроллера с передачей объекта request
        start_response(code, [('Content-Type', content_type)])
        return [body]

    @staticmethod
    def get_content_type(file_path, content_types_map=CONTENT_TYPES_MAP):
        file_name = path.basename(file_path).lower()  # styles.css
        extension = path.splitext(file_name)[1]  # .css
        return content_types_map.get(extension, "text/html")

    @staticmethod
    def get_static(static_dir, file_path):
        path_to_file = path.join(static_dir, file_path)
        with open(path_to_file, 'rb') as f:
            file_content = f.read()
        status_code = '200 OK'
        return status_code, file_content

    @staticmethod
    def decode_value(data):
        new_data = {}
        for k, v in data.items():
            val = bytes(v.replace('%', '=').replace("+", " "), 'UTF-8')
            val_decode_str = decodestring(val).decode('UTF-8')
            new_data[k] = val_decode_str
        return new_data

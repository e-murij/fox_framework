from wsgiref.simple_server import make_server

from fox_framework.main import Framework
from patterns.generative_patterns import Logger
from patterns.structural_patterns import routes_from_decorator
from urls import routes_from_urls, fronts
from components import settings

logger_to_file = Logger('site')
all_routes = {**routes_from_urls, **routes_from_decorator}
application = Framework(all_routes, fronts, settings)

with make_server('', 8000, application) as httpd:
    logger_to_file.log('Running on port 8000...')
    print("Запуск на порту 8000...")
    httpd.serve_forever()

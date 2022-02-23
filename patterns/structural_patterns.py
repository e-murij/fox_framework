from time import time


routes_from_decorator = {}


# Декоратор
class AppRoute:
    def __init__(self, url):
        self.url = url

    def __call__(self, cls):
        routes_from_decorator[self.url] = cls()


# Декоратор
class Debug:

    def __call__(self, cls):
        def timeit(method):
            def timed(*args, **kwargs):
                time_start = time()
                result = method(*args, **kwargs)
                time_end = time()
                time_result = time_end - time_start
                print(f'{str(cls).split()[1]} выполнялся {time_result:.3f}')
                return result
            return timed
        return timeit(cls)

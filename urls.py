from datetime import date
from views import *


# front controller
def secret_front(request):
    request['date'] = date.today()


# front controller
def other_front(request):
    request['key'] = 'key'


fronts = [secret_front, other_front]

routes_from_urls = {
    # '/': Index(),
    # '/about/': About(),
    # '/contact/': Contact(),
    '/create_category/': CreateCategory(),
    '/course-list/': CourseList(),
    '/create-course/': CreateCourse(),
    '/course-copy/': CopyCourse(),
    '/ex/': Example()
}
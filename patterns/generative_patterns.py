import os
from copy import deepcopy
from quopri import decodestring
from sqlite3 import connect

from components.settings import DATABASE
from patterns.architectural_system_patterns import BaseMapper, DomainObject
from patterns.behavioral_patterns import Subject, FileWriter


# Прототип
class CoursePrototype:
    """ Прототип курсов обучения"""
    def clone(self):
        return deepcopy(self)


class AbstractCourse(CoursePrototype, Subject):
    """ Абстрактный курс """
    def __init__(self, **kwargs):
        super().__init__()
        if 'id' in kwargs:
            self.id = kwargs.get('id')
        if 'name' in kwargs:
            self.name = kwargs.get('name')
        if 'category_id' in kwargs:
            self.category_id = kwargs.get('category_id')


class OnlineCourse(AbstractCourse, DomainObject):
    pass


class OfflineCourse(AbstractCourse, DomainObject):
    pass


# Фабричный метод
class CourseFactory:
    """ Фабрика курсов"""
    types = {
        'online': OnlineCourse,
        'offline': OfflineCourse,
    }

    @classmethod
    def create(cls, type_, **kwargs):
        return cls.types[type_](**kwargs)


class AbstractUser:
    """ Абстрактный пользователь """
    def __init__(self, **kwargs):
        if 'name' in kwargs:
            self.name = kwargs.get('name')

        if 'id' in kwargs:
            self.id = kwargs.get('id')


class Teacher(AbstractUser):
    """ Преподаватель """
    pass


class Student(AbstractUser, DomainObject):
    """ Студент """
    pass


# Фабричный метод
class UserFactory:
    """ Фабрика пользователей"""
    types = {
        'teacher': Teacher,
        'student': Student
    }

    @classmethod
    def create(cls, type_, **kwargs):
        return cls.types[type_](**kwargs)


class Category(DomainObject):
    """ Категории курсов"""

    def __init__(self, **kwargs):
        if 'name' in kwargs:
            self.name = kwargs.get('name')

        if 'id' in kwargs:
            self.id = kwargs.get('id')


class StudentOnlineCourse(DomainObject):
    """ Запись студента на онлайн курс"""

    def __init__(self, **kwargs):
        if 'student_id' in kwargs:
            self.student_id = kwargs.get('student_id')

        if 'course_id' in kwargs:
            self.course_id = kwargs.get('course_id')


class StudentOfflineCourse(DomainObject):
    """ Запись студента на оффлайн курс"""

    def __init__(self, **kwargs):
        if 'student_id' in kwargs:
            self.student_id = kwargs.get('student_id')

        if 'course_id' in kwargs:
            self.course_id = kwargs.get('course_id')


# Синглтон
class SingletonName(type):

    def __init__(cls, name, bases, attrs, **kwargs):
        super().__init__(name, bases, attrs)
        cls.__instance = {}

    def __call__(cls, *args, **kwargs):
        name = None
        if args:
            name = args[0]
        if kwargs:
            name = kwargs['name']

        if name and name in cls.__instance:
            return cls.__instance[name]
        else:
            cls.__instance[name] = super().__call__(*args, **kwargs)
            return cls.__instance[name]


class Logger(metaclass=SingletonName):
    """ Логгер с одним и тем же именем пишет данные в один и тот же файл, а с другим именем в другой """
    def __init__(self, name, writer=FileWriter()):
        self.name = name
        self.writer = writer

    def log(self, text):
        self.writer.write(text)


class Engine:
    """ Основной интерфейс проекта"""

    @staticmethod
    def create_user(type_):
        return UserFactory.create(type_)

    @staticmethod
    def create_category():
        return Category()

    @staticmethod
    def create_course(type_):
        return CourseFactory.create(type_)

    @staticmethod
    def create_student_online_course():
        return StudentOnlineCourse()

    @staticmethod
    def create_student_offline_course():
        return StudentOfflineCourse()

    @staticmethod
    def decode_value(val):
        val_b = bytes(val.replace('%', '=').replace("+", " "), 'UTF-8')
        val_decode_str = decodestring(val_b)
        return val_decode_str.decode('UTF-8')


class StudentMapper(BaseMapper):
    tablename = 'students'
    model = Student


class CategoryMapper(BaseMapper):
    tablename = 'categories'
    model = Category


class OnlineCourseMapper(BaseMapper):
    tablename = 'online_course'
    model = OnlineCourse


class OfflineCourseMapper(BaseMapper):
    tablename = 'offline_course'
    model = OfflineCourse


class StudentOnLineCourseMapper(BaseMapper):
    tablename = 'student_onlinecourse'
    model = StudentOnlineCourse


class StudentOffLineCourseMapper(BaseMapper):
    tablename = 'student_offlinecourse'
    model = StudentOfflineCourse


connection = connect(DATABASE)


class MapperRegistry:
    mappers = {
        'student': StudentMapper,
        'category': CategoryMapper,
        'online': OnlineCourseMapper,
        'offline': OfflineCourseMapper,
        'student_onlinecourse': StudentOnLineCourseMapper,
        'student_offlinecourse': StudentOffLineCourseMapper
    }

    @staticmethod
    def get_mapper(obj):
        if isinstance(obj, Student):
            return StudentMapper(connection)
        elif isinstance(obj, Category):
            return CategoryMapper(connection)
        elif isinstance(obj, OnlineCourse):
            return OnlineCourseMapper(connection)
        elif isinstance(obj, OfflineCourse):
            return OfflineCourseMapper(connection)
        elif isinstance(obj, StudentOnlineCourse):
            return StudentOnLineCourseMapper(connection)
        elif isinstance(obj, StudentOfflineCourse):
            return StudentOffLineCourseMapper(connection)

    @staticmethod
    def get_current_mapper(name):
        return MapperRegistry.mappers[name](connection)

from fox_framework.templator import render
from patterns.architectural_system_patterns import UnitOfWork
from patterns.behavioral_patterns import ListView, CreateView, EmailNotifier, SmsNotifier, BaseSerializer, \
    ConsoleWriter
from patterns.generative_patterns import Engine, Logger, CourseFactory, MapperRegistry
from patterns.structural_patterns import AppRoute, Debug

site_engine = Engine()
logger_to_file = Logger('file')
logger_to_console = Logger('console', ConsoleWriter())
email_notifier = EmailNotifier()
sms_notifier = SmsNotifier()
UnitOfWork.new_current()
UnitOfWork.get_current().set_mapper_registry(MapperRegistry)


@AppRoute('/')
class Index:
    @Debug()
    def __call__(self, request):
        logger_to_file.log('loading Index')
        logger_to_console.log('loading Index')
        mapper = MapperRegistry.get_current_mapper('category')
        return '200 OK', render('index.html',date=request.get('date', None), categories=mapper.all())


@AppRoute('/contact/')
class Contact:
    @Debug()
    def __call__(self, request):
        logger_to_file.log('loading Contacts')
        logger_to_console.log('loading Contacts')
        return '200 OK', render('contact.html', date=request.get('date', None))


@AppRoute('/about/')
class About:
    @Debug()
    def __call__(self, request):
        logger_to_file.log('loading About')
        logger_to_console.log('loading About')
        return '200 OK', render('about.html', date=request.get('date', None))


class CreateCategory(CreateView):
    template_name = 'create_category.html'

    def create_obj(self, data: dict):
        name = data.get('name')
        name = site_engine.decode_value(name)
        new_category = site_engine.create_category()
        schema = {'name': name}
        new_category.mark_new(schema)
        UnitOfWork.get_current().commit()


class CourseList:
    @Debug()
    def __call__(self, request):
        try:
            mapper_category = MapperRegistry.get_current_mapper('category')
            category = mapper_category.get_by_id(int(request['request_params']['id']))
            mapper_online = MapperRegistry.get_current_mapper('online')
            mapper_offline = MapperRegistry.get_current_mapper('offline')
            all_course_list = mapper_online.all() + mapper_offline.all()
            course_list = [course for course in all_course_list if course.category_id == category.id]
            logger_to_file.log('loading courses list')
            return '200 OK', render('course_list.html',
                                    course_list=course_list,
                                    category_name=category.name, id=category.id,
                                    )
        except (KeyError, ValueError):
            return '200 OK', 'No courses have been added yet'


class CreateCourse:
    @Debug()
    def __call__(self, request):
        if request['method'] == 'POST':
            data = request['data']
            name = data['name']
            type = data['type']
            name = site_engine.decode_value(name)
            mapper = MapperRegistry.get_current_mapper('category')
            category = mapper.get_by_id(self.category_id)
            course = site_engine.create_course(type)
            schema = {'name': name, 'category_id': str(category.id)}
            course.mark_new(schema)
            UnitOfWork.get_current().commit()
            course.name = name
            course.category_id = category.id
            course.observers.append(email_notifier)
            course.observers.append(sms_notifier)
            course.notify()
            logger_to_file.log('new course added')
            return '200 OK', render('create_course.html',
                                    category_name=category.name,
                                    types_course_list=CourseFactory.types.keys(),
                                    id=category.id,
                                    )
        else:
            try:
                self.category_id = int(request['request_params']['id'])
                mapper = MapperRegistry.get_current_mapper('category')
                category = mapper.get_by_id(self.category_id)
                return '200 OK', render('create_course.html',
                                        category_name=category.name,
                                        types_course_list=CourseFactory.types.keys(),
                                        id=category.id)
            except (KeyError, ValueError):
                return '200 OK', 'Неверно указана категория курса'


class CopyCourse:
    @Debug()
    def __call__(self, request):
        data = request['request_params']
        try:
            category_id = data['category_id']
            name = data['name']
            name = site_engine.decode_value(name)
            mapper_online = MapperRegistry.get_current_mapper('online')
            mapper_offline = MapperRegistry.get_current_mapper('offline')
            all_course_list = mapper_online.all() + mapper_offline.all()
            course_for_copy = None
            for course in all_course_list:
                print(course.name, )
                if course.name == name and course.category_id == int(category_id):
                    course_for_copy = course
            print(course_for_copy)
            if course_for_copy:
                new_course = course_for_copy.clone()
                new_course.name = f'copy_{name}'
                schema = {'name': new_course.name, 'category_id': str(new_course.category_id)}
                new_course.mark_new(schema)
                UnitOfWork.get_current().commit()
                new_course.notify()
            all_course_list = mapper_online.all() + mapper_offline.all()
            course_list = [course for course in all_course_list if course.category_id == int(category_id)]
            mapper_category = MapperRegistry.get_current_mapper('category')
            category = mapper_category.get_by_id(category_id)
            return '200 OK', render('course_list.html',
                                    course_list=course_list,
                                    category_name=category.name,
                                    id=category_id,
                                    )
        except (KeyError, ValueError):
            return '200 OK', 'Неверно указана категория курса'


class Example:
    def __call__(self, request):
        return '200 OK', render('examples.html')


@AppRoute('/students-list/')
class StudentList(ListView):
    template_name = 'students_list.html'
    context_object_name = 'student_list'

    def get_queryset(self):
        mapper = MapperRegistry.get_current_mapper('student')
        return mapper.all()


@AppRoute('/create-student/')
class StudentCreate(CreateView):
    template_name = 'create_student.html'

    def create_obj(self, data: dict):
        name = data.get('name')
        name = site_engine.decode_value(name)
        new_obj = site_engine.create_user('student')
        schema = {'name': name}
        new_obj.mark_new(schema)
        UnitOfWork.get_current().commit()


@AppRoute('/add-student/')
class AddStudentByCourse(CreateView):
    template_name = 'add_student.html'

    def get_context_data(self):
        context = super().get_context_data()
        mapper_online = MapperRegistry.get_current_mapper('online')
        mapper_offline = MapperRegistry.get_current_mapper('offline')
        all_course_list = mapper_online.all() + mapper_offline.all()
        mapper_student = MapperRegistry.get_current_mapper('student')
        all_students = mapper_student.all()
        context['course_list'] = all_course_list
        context['student_list'] = all_students
        return context

    def create_obj(self, data):
        course_name = data['course']
        course_name = site_engine.decode_value(course_name)
        student_name = data['student']
        student_name = site_engine.decode_value(student_name)
        mapper_online = MapperRegistry.get_current_mapper('online')
        mapper_offline = MapperRegistry.get_current_mapper('offline')
        mapper_student = MapperRegistry.get_current_mapper('student')
        all_students = mapper_student.all()
        for student in all_students:
            if student.name == student_name:
                student_id = student.id
        for course in mapper_online.all():
            if course.name == course_name:
                course_id = course.id
                new_obj = site_engine.create_student_online_course()
                schema = {'student_id': student_id, 'course_id': course_id}
                new_obj.mark_new(schema)
                UnitOfWork.get_current().commit()
                return
        for course in mapper_offline.all():
            if course.name == course_name:
                course_id = course.id
                new_obj = site_engine.create_student_offline_course()
                schema = {'student_id': student_id, 'course_id': course_id}
                new_obj.mark_new(schema)
                UnitOfWork.get_current().commit()


@AppRoute('/api/')
class CourseApi:
    @Debug()
    def __call__(self, request):
        mapper_online = MapperRegistry.get_current_mapper('online')
        mapper_offline = MapperRegistry.get_current_mapper('offline')
        all_course_list = mapper_online.all() + mapper_offline.all()
        return '200 OK', BaseSerializer(all_course_list).save()

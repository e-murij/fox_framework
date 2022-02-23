import threading
from abc import ABCMeta, abstractmethod


class UnitOfWork:
    """
    Паттерн UNIT OF WORK
    """
    current = threading.local()

    def __init__(self):
        self.new_objects = []
        self.dirty_objects = []
        self.removed_objects = []

    def set_mapper_registry(self, MapperRegistry):
        self.MapperRegistry = MapperRegistry

    def register_new(self, object, schema):
        self.new_objects.append({'object': object, 'schema': schema})

    def register_dirty(self, object, schema):
        self.dirty_objects.append({'object': object, 'schema': schema})

    def register_removed(self, object):
        self.removed_objects.append(object)

    def commit(self):
        self.insert_new()
        self.update_dirty()
        self.delete_removed()

    def insert_new(self):
        for object in self.new_objects:
            self.MapperRegistry.get_mapper(object['object']).insert(
                **object['schema'])

        self.new_objects.clear()

    def update_dirty(self):
        for object in self.dirty_objects:
            self.MapperRegistry.get_mapper(object['object']).insert(
                object['object'], **object['schema'])

        self.dirty_objects.clear()

    def delete_removed(self):
        for object in self.removed_objects:
            self.MapperRegistry.get_mapper(object).delete(object)

        self.removed_objects.clear()

    @staticmethod
    def new_current():
        __class__.set_current(UnitOfWork())

    @classmethod
    def set_current(cls, unit_of_work):
        cls.current.unit_of_work = unit_of_work

    @classmethod
    def get_current(cls):
        return cls.current.unit_of_work


class DomainObject:

    def mark_new(self, schema):
        UnitOfWork.get_current().register_new(self, schema)

    def mark_dirty(self, schema):
        UnitOfWork.get_current().register_dirty(self, schema)

    def mark_removed(self):
        UnitOfWork.get_current().register_removed(self)


class BaseMapper(metaclass=ABCMeta):
    """Преобразователь данных (Data Mapper)"""

    def __init__(self, connection) -> None:
        self.connection = connection
        self.cursor = connection.cursor()

    @property
    @abstractmethod
    def tablename(self):
        pass

    @property
    @abstractmethod
    def model(self):
        pass

    def all(self):
        statement = f'SELECT * from {self.tablename}'
        self.cursor.execute(statement)
        column_names = [description_info[0] for description_info in self.cursor.description]
        result = []

        for values in self.cursor.fetchall():
            object = self.model(**{column_names[i]: values[i] for i, _ in enumerate(values)})
            result.append(object)
        return result

    def insert(self, **schema):
        statement = f"INSERT INTO {self.tablename} ({','.join(schema.keys())}) VALUES ({str('?, ' * len(schema.keys()))[:-2]})"
        self.cursor.execute(statement, tuple(schema.values()))
        try:
            self.connection.commit()
        except Exception as e:
            raise DbCommitException(e.args)

    def update(self, object, **schema):
        schema = {str(key) + '=?': value for key, value in schema.items()}
        statement = f"UPDATE {self.tablename} SET {','.join(schema.keys())} WHERE id=?"
        self.cursor.execute(statement, (','.join(schema.values()), object.id))
        try:
            self.connection.commit()
        except Exception as e:
            raise DbUpdateException(e.args)

    def delete(self, object):
        statement = f"DELETE FROM {self.tablename} WHERE id=?"
        self.cursor.execute(statement, (object.id,))
        try:
            self.connection.commit()
        except Exception as e:
            raise DbDeleteException(e.args)

    def get_by_id(self, id):
        statement = f"SELECT * FROM {self.tablename} WHERE id=?"
        self.cursor.execute(statement, (id,))
        result = self.cursor.fetchone()
        try:
            id, name = result
            return self.model(id=id, name=name)
        except Exception as e:
            raise RecordNotFoundException(f'Record with id={id} not found')


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

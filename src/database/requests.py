import pymysql
import pymysql.cursors
from config.sql_query import ADD_STUDENT, SELECT_ALL_PERSONS, SELECT_STUDENT, SELECT_TUTOR, SELECT_STUDENTS_BY_TUTOR
from .database_property import DBProperties

class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]
class Database(metaclass=Singleton):
    connection = None
    properties = DBProperties()
    def connect_db(self):
        if self.connection is None:
            print("Создание нового подключения к бд")
            try:
                self.connection = pymysql.connect(
                    host=self.properties.get_host(),
                    port=self.properties.get_port(),
                    user=self.properties.get_user(),
                    password=self.properties.get_password(),
                    database=self.properties.get_db_name(),
                    cursorclass=pymysql.cursors.DictCursor
                )
            except Exception as ex:
                print(ex)
    def execute(self, query: str):
        result = None
        try:
            with self.connection.cursor() as cursor:
                    cursor.execute(query)
            self.connection.commit()
            result = cursor.fetchall()
        except Exception as ex:
            print(ex)
        finally:
            return result

def add_new_student(student_id: int, tutor_id: int, user_name: str, name: str) -> None:
    query = ADD_STUDENT.format(student_id, tutor_id, user_name, name)
    Database().execute(query)

def select_all_persons(role: str):
    db = Database()
    result = None
    if role == "tutor":
        result = db.execute(SELECT_ALL_PERSONS.format("tutors"))
    elif role == "student":
        result = db.execute(SELECT_ALL_PERSONS.format("students"))
    return result

def select_person(user_id: int, role: str):
    db = Database()
    result = None
    if role == "tutor":
        result = db.execute(SELECT_TUTOR.format(user_id))
    elif role == "student":
        result = db.execute(SELECT_STUDENT.format(user_id))
    return result

def select_person_by_tutor(tutor_name: str):
    return Database().execute(SELECT_STUDENTS_BY_TUTOR.format(tutor_name))





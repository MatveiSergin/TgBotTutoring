import pymysql
import pymysql.cursors
from config.sql_query import *
from .database_property import DBProperties

class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]
class Database(metaclass=Singleton):
    connection = None
    def __init__(self):
        if self.connection is None:
            print("Создание нового подключения к бд")
            self.properties = DBProperties()
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
                print(1, ex)
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

def add_new_dz(student_id: int, path_to_file: str):
    Database().execute(ADD_NEW_DZ.format(count_dz_for_student(student_id), student_id, path_to_file))

def select_last_dz_id(student_id: int):
    return Database().execute(SELECT_LAST_DZ_ID.format(student_id))

def add_answer_for_dz(dz_id: int, student_id: int, task_number: int, answer: str):
    Database().execute(ADD_ANSWER_FOR_DZ.format(dz_id, student_id, task_number, answer))

def select_dz_by_number(number_dz: int, student_id: int):
    return Database().execute(SELECT_DZ.format(number_dz, student_id))

def count_answers_for_dz(dz_id: int, student_id: int):
    return Database().execute(COUNT_ANSWERS_FOR_DZ.format(dz_id, student_id))[0]['COUNT(task_number)']
def select_answers(dz_id: int, student_id: int):
    count = count_answers_for_dz(dz_id, student_id)
    answers = []
    for i in range(1, count + 1):
        answers.append(f"{i}: {Database().execute(SELECT_ANSWER.format(dz_id, student_id, i))[0]['answer']}")
    return answers

def count_dz_for_student(student_id: int):
    return Database().execute(COUNT_DZ_FOR_STUDENT.format(student_id))[0]["COUNT(id)"]
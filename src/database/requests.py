import pymysql
import pymysql.cursors

from config.properties import Singleton
from config.sql_query import *
from .database_property import DBProperties

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

    if result:
        return result[0]
    else:
        return None

def select_person_by_tutor(tutor_name: str):
    return Database().execute(SELECT_STUDENTS_BY_TUTOR.format(tutor_name))

def add_new_dz(student_id: int, path_to_file: str):
    Database().execute(ADD_NEW_DZ.format(count_dz_for_student(student_id), student_id, path_to_file))

def select_last_dz_id(student_id: int):
    select = Database().execute(SELECT_LAST_DZ_ID.format(student_id))
    if select:
        return Database().execute(SELECT_LAST_DZ_ID.format(student_id))[0]["id"]
    else:
        return 0

def add_answer_for_dz(dz_id: int, student_id: int, task_number: int, answer: str):
    Database().execute(ADD_ANSWER_FOR_DZ.format(dz_id, student_id, task_number, answer))

def select_path_for_dz_by_number(number_dz: int, student_id: int):
    return Database().execute(SELECT_PATH_FOR_DZ.format(number_dz, student_id))

def count_answers_for_dz(dz_id: int, student_id: int):
    return Database().execute(COUNT_ANSWERS_FOR_DZ.format(dz_id, student_id))[0]['COUNT(task_number)']
def select_answers(dz_id: int, student_id: int):
    count = count_answers_for_dz(dz_id, student_id)
    answers = {}
    for i in range(1, count + 1):
        answers[i] = Database().execute(SELECT_ANSWER.format(dz_id, student_id, i))[0]['cur_answer']
    return answers

def count_dz_for_student(student_id: int):
    return Database().execute(COUNT_DZ_FOR_STUDENT.format(student_id))[0]["COUNT(id)"]

def select_student_by_name(student_name: str):
    return Database().execute(SELECT_STUDENT_BY_NAME.format(student_name))[0]["student_id"]

def update_answers_for_dz(student_name: str, dz_id: int, task_number: int, cur_ans: str):
    student_id = select_student_by_name(student_name)
    Database().execute(UPDATE_ANSWERS_FOR_DZ.format(cur_ans, dz_id, student_id, task_number))

def select_path_to_file(dz_id: int, student_name: str):
    student_id = int(select_student_by_name(student_name))
    return Database().execute(SELECT_PATH_TO_FILE.format(student_id, dz_id))[0]['path_to_file']
def delete_dz(dz_id: int, student_name: str):
    student_id = int(select_student_by_name(student_name))
    Database().execute(DELETE_DZ.format(dz_id, student_id))

def change_has_answer_in_dz(dz_id: int, student_id: int):
    Database().execute(CHANGE_HAS_ANSWER_IN_DZ.format(dz_id, student_id))

def select_has_answer_in_dz(dz_id: int, student_id: int):
    return Database().execute(SELECT_HAS_ANSWER_IN_DZ.format(dz_id, student_id))[0]['has_answers']

def update_answer_in_answers(dz_id: int, student_id: int, answers: list[str]):
    for task_number in range(1, len(answers) + 1):
        Database().execute(UPDATE_ANSWER_IN_ANSWERS.format(answers[task_number - 1], task_number, dz_id, student_id))

def add_additional_files(dz_id: int, student_id: int, path_to_file: str):
    Database().execute(ADD_NEW_ADDITIONAL_FILES.format(dz_id, student_id, path_to_file))
    Database().execute(UPDATE_HAS_ADDITIONAL_FILE.format(dz_id, student_id))

def update_message_id_for_dz(message_id:int, dz_id: int, student_id: int):
    Database().execute(ADD_MESSAGE_ID_FOR_DZ.format(message_id, dz_id, student_id))

def select_dz(dz_id: int, student_id: int):
    return Database().execute(SELECT_DZ.format(dz_id, student_id))[0]

def update_counter_dz(counter_dz:int, dz_id: int, student_id: int):
    Database().execute(UPDATE_COUNTER_DZ.format(counter_dz, dz_id, student_id))

def update_remark_for_dz(remark: str, dz_id: int, student_id: int):
    Database().execute(UPDATE_REMARK_FOR_DZ.format(remark, dz_id, student_id))
from database.requests import select_all_persons, select_person, add_new_student, select_person_by_tutor
class Student():

    def __init__(self, user_id: int):
        self.user_id = user_id
        self.role = 'student'
    def isvalid(self):
        students = select_person(self.user_id, self.role)
        return students is not None

    def register(self, tutor_name: str, user_name: str, name: str):
        self.user_name = user_name
        self.name = name
        self.tutor_id = filter(lambda x: x["name"] == tutor_name, select_all_persons("tutor")).next()["tutor_id"]
        try:
            add_new_student(self.user_id, self.tutor_id, self.user_name, self.name)
        except Exception as ex:
            print("add_new_person dont add new person", ex)


class Tutor():
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.role = 'tutor'

    def isvalid(self):
        data = select_person(self.user_id, self.role)
        return data is not None

    def get_students(self):
        pass
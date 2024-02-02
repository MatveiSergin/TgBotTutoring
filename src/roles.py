from database.requests import select_all_persons, select_person, add_new_student, select_person_by_tutor
class Student():
    def __init__(self, student_id: int):
        self.user_id = student_id
        self.role = 'student'

        self.isval = self.isvalid()
        if self.isval:
            student = select_person(self.user_id, self.role)
            self.user_name = student['user_name']
            self.name = student['name']
            self._tutor_id = student['tutor_id']
    def isvalid(self) -> bool:
        students = select_person(self.user_id, self.role)
        return bool(students)

    def register(self, user_name: str, tutor_name: str, name: str):
        self.user_name = user_name
        self.name = name
        try:
            self._tutor_id = next(filter(lambda x: x["name"][:-2].lower() == tutor_name, select_all_persons("tutor")))["tutor_id"]
        except StopIteration:
            print("нету учителя епт")
        try:
            add_new_student(self.user_id, self._tutor_id, self.user_name, self.name)
        except Exception as ex:
            print("add_new_person dont add new person", ex)

    def get_tutor(self):
        data = select_person(self._tutor_id, 'tutor')
        tutor = Tutor(int(data['tutor_id']))
        return tutor

class Tutor():
    def __init__(self, tutor_id: int):
        self.user_id = tutor_id
        self.role = 'tutor'
        data = select_person(self.user_id, self.role)
        self.isval = bool(data)
        if self.isval:
            self.name = data["name"]
    def isvalid(self) -> bool:
        return self.isval

    def get_students(self) -> set[Student]:
        if not self.isval:
            return set()
        students = set(Student(int(student_id)) for student_id in map(lambda x: x['student_id'], select_person_by_tutor(self.name)))
        return students
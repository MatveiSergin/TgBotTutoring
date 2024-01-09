from roles import Student, Tutor
class Action():

    def __init__(self, person: Student | Tutor):
        self.person = person

    def get_last_dz(self):
        pass
    def get_all_dz(self):
        pass

    def check_dz(self):
        pass

    def get_manual(self):
        pass

    def download_task(self, student_id: int, ):
        pass
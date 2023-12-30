ADD_STUDENT = "INSERT INTO students (user_id, tutor_id, user_name, name) VALUES ({0}, '{1}', '{2}', '{3}');"

SELECT_ALL_PERSONS = """
SELECT * FROM {0};
"""

SELECT_STUDENT = """
SELECT * FROM students
WHERE student_id = {0};
"""

SELECT_TUTOR = """
SELECT * FROM tutors
WHERE tutor_id = {0};
"""

SELECT_STUDENTS_BY_TUTOR = """
SELECT student_id, name FROM students
WHERE tutor_id = (SELECT tutor_id FROM tutors WHERE name = {});
"""

ADD_NEW_DZ = """
INSERT INTO dz 
(user_id, path_to_file, creation_at)
VALUES
({0}, {1}, now());
"""

ADD_ANSWERS_FOR_DZ = """
INSERT INTO answers
(dz_id, task_number)
VALUES
({0}, {1}) 
"""
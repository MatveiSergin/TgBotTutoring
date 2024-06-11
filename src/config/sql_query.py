ADD_STUDENT = "INSERT INTO students (student_id, tutor_id, user_name, name) VALUES ({0}, '{1}', '{2}', '{3}');"

SELECT_ALL_PERSONS = """
SELECT * FROM {0};
"""

SELECT_STUDENT = """
SELECT * FROM students
WHERE student_id = {0};
"""

SELECT_STUDENT_BY_NAME = """
SELECT student_id FROM students
WHERE name = '{0}';
"""

SELECT_TUTOR = """
SELECT * FROM tutors
WHERE tutor_id = {0};
"""

SELECT_STUDENTS_BY_TUTOR = """
SELECT student_id, name FROM students
WHERE tutor_id = (SELECT tutor_id FROM tutors WHERE name = '{}');
"""

ADD_NEW_DZ = """
INSERT INTO dz 
(id, student_id, path_to_file, creation_at)
VALUES
(({0} + 1), {1}, '{2}', now());
"""


ADD_ANSWER_FOR_DZ = """
INSERT INTO answers
(dz_id, student_id, task_number, cur_answer)
VALUES
({0}, {1}, {2}, '{3}');
"""

SELECT_LAST_DZ_ID = """
SELECT id FROM dz
WHERE student_id = {0}
ORDER BY id DESC
LIMIT 1;
"""

COUNT_DZ_FOR_STUDENT = """
SELECT COUNT(id) FROM dz
WHERE student_id = {0};
"""

SELECT_PATH_FOR_DZ = """
SELECT path_to_file FROM dz
WHERE id = {0} AND student_id = {1};
"""

SELECT_ANSWER = """
SELECT cur_answer FROM answers
WHERE dz_id = {0} AND student_id = {1} AND task_number = {2};
"""

COUNT_ANSWERS_FOR_DZ = """
SELECT COUNT(task_number) FROM answers
WHERE dz_id = {0} AND student_id = {1};
"""

UPDATE_ANSWERS_FOR_DZ = """
UPDATE answers
SET cur_answer = '{0}'
WHERE dz_id = {1} AND student_id = {2} AND task_number = {3};
"""

SELECT_PATH_TO_FILE = """
SELECT path_to_file FROM dz
WHERE student_id = {0} AND id = {1};
"""

DELETE_DZ = """
DELETE FROM dz
WHERE id = {0} AND student_id = {1};
"""

CHANGE_HAS_ANSWER_IN_DZ = """
UPDATE dz
SET has_answers = true
WHERE id = {0} AND student_id = {1};
"""

SELECT_HAS_ANSWER_IN_DZ = """
SELECT has_answers FROM dz
WHERE id = {0} AND student_id = {1};
"""

UPDATE_ANSWER_IN_ANSWERS = """
UPDATE answers
SET answer = '{0}'
WHERE task_number = {1} AND dz_id  = {2} AND student_id  = {3};
"""

ADD_NEW_ADDITIONAL_FILES = """
INSERT INTO additional_files 
(dz_id, student_id, path_to_file)
VALUES
({0}, {1}, '{2}');
"""

ADD_MESSAGE_ID_FOR_DZ = """
UPDATE dz
SET message_id = {0}
WHERE id = {1} AND student_id = {2};
"""

SELECT_DZ = """
SELECT * FROM dz
WHERE id = {0} AND student_id = {1};
"""

UPDATE_COUNTER_DZ = """
UPDATE dz
SET counter_dz = {0}
WHERE id = {1} AND student_id = {2};
"""

UPDATE_REMARK_FOR_DZ = """
UPDATE dz
SET remark = '{0}'
WHERE id = {1} AND student_id = {2};
"""

UPDATE_HAS_ADDITIONAL_FILE = """
UPDATE dz
SET has_additional_file = true
WHERE id = {0} AND student_id = {1};
"""

SELECT_CUR_ANSWER = """
SELECT cur_answer FROM dz
WHERE id = {0} AND student_id = {1};
"""

SELECT_STUDENT_ANSWER = """
SELECT answer FROM dz
WHERE id = {0} AND student_id = {1};
"""

SELECT_CREATION_DATA_FOR_DZ = """
SELECT creation_at FROM dz
WHERE id = (SELECT id FROM dz
            WHERE student_id = {0}
            ORDER BY id DESC
            LIMIT 1) AND student_id = {0};
"""

UPDATE_NAV_MESSAGE_ID_FOR_TUTUR = """
UPDATE tutors
SET navigation_message_id = {0}
WHERE tutor_id = {1};
"""

SELECT_NAV_MESSAGE_ID = """
SELECT navigation_message_id FROM tutors
WHERE tutor_id = {0};
"""
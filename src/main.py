import time
import telebot as tb
import os
from datetime import datetime
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, Message

from config.properties import TelebotProperties
from files import Files
from roles import Student, Tutor
from database.requests import *
import threading

class Deleting_telebot(tb.TeleBot):
    def send_message(self, *args, is_deleting: bool = True, **kwargs) -> Message:
        msg = super().send_message(*args, **kwargs)
        if is_deleting:
            thr = threading.Thread(target=delete_message_with_delay, args=(msg, ))
            thr.start()
        return msg
    def send_document(self, *args, is_deleting: bool = True, **kwargs) -> Message:
        msg = super().send_document(*args, **kwargs)
        if is_deleting:
            thr = threading.Thread(target=delete_message_with_delay, args=(msg, ))
            thr.start()
        return msg
    def process_new_messages(self, new_messages):
        thr = threading.Thread(target=delete_message_with_delay, args=(new_messages[0],))
        thr.start()
        super().process_new_messages(new_messages)



bot = Deleting_telebot(token=TelebotProperties().get_token())

def delete_message_with_delay(message):
    time.sleep(3600)
    bot.delete_message(message.chat.id, message.id)

@bot.message_handler(commands=["start"])
def welcome(message: Message):
    user_id = message.chat.id
    person = init_person(message)

    if person.isval:
        bot.send_message(user_id, text="Привет!")
        navigation(message, person)
        return


@bot.message_handler(commands=["nav"])
def navigation(message: Message, person: Student | None | Tutor = None):
    if person is None:
        person = init_person(message)

    if isinstance(person, Tutor):
        navigation_for_tutor(message, person)
    elif isinstance(person, Student):
        navigation_for_student(message, person)


@bot.message_handler(commands=["mistake"])
def navigation_with_mistakes(message: Message, person: None | Tutor = None):
    def get_info(person: Tutor):
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        button1 = KeyboardButton(text="Изменить ответ")
        button2 = KeyboardButton(text="Прикрепить новый файл")
        button3 = KeyboardButton(text="Удалить домашнюю работу")
        button4 = KeyboardButton(text="Назад")
        keyboard.add(button1, button2, button3, button4)
        msg = bot.send_message(person.user_id, text="Выберите действие, которое необходимо выполнить:",
                               reply_markup=keyboard)
        
        bot.register_next_step_handler(msg, define_mistake, person)

    def define_mistake(message: Message, person: Tutor):
        text = message.text
        if text == "Назад":
            navigation(message, person)
        elif text == "Изменить ответ":
            msg = bot.send_message(person.user_id, text="Если вы ввели не правильно один из ответов"
                                                  " в домашней работе вам следует:\n"
                                                  " 1) выбрать ученика. При желании можно "
                                                  "посмотреть при помощи команды /my_students\n"
                                                  " 2) выбрать номер домашней работы."
                                                  " При желнии можно просмотреть "
                                                  "ее содержимое командой: /get_dz\n "
                                                  "3) Выбрать номер ответа, который "
                                                  "следует отредактировать. При желании "
                                                  "можно просмотреть все правильные ответы "
                                                  "для дз при помощи команды: /get_answer")
            
            msg = bot.send_message(person.user_id, text="Введите одной строкой данную информацию.\n"
                                                  "Например: <strong>Иван И dz-1 ans-1: 123</strong>\n"
                                                  "Здесь <i>'Иван И'</i> - имя и фамилия ученика;\n"
                                                  "<i>'dz-1'</i> - номер домашней работы;\n"
                                                  "<i>'ans-1'</i> - номер ответа;\n"
                                                  "<i>'123'</i> - правильный ответ.", parse_mode="HTML")
            
            bot.register_next_step_handler(msg, update_answer, person)
        elif text in ("Прикрепить новый файл", "Удалить домашнюю работу"):
            msg = bot.send_message(person.user_id, text="Для данного действия вам необходимо:\n"
                                                  "1) выбрать ученика (при желании можно "
                                                  "посмотреть при помощи команды /my_students\n"
                                                  "2) выбрать номер домашней работы"
                                                  " (при желнии можно просмотреть "
                                                  "ее содержимое командой: /get_dz\n")
            
            msg = bot.send_message(person.user_id, text="Введите одной строкой данную информацию.\n"
                                                  "Например: <b>Иван И dz-1</b>\n"
                                                  "Здесь <i>'Иван И'</i> - имя и фамилия ученика;\n"
                                                  "<i>'dz-1'</i> - номер домашней работы/", parse_mode="HTML")
            
            bot.register_next_step_handler(msg, update_dz, person, is_delete=(text == "Удалить домашнюю работу"))

    def update_answer(message: Message, person: Tutor):
        text = message.text
        t = text.split()
        if text == "/my_students":
            get_list_students(message, person)
            return
        elif text == "/get_dz":
            get_dz_for_tutor(message, person)
            return
        elif text == "/get_answer":
            get_answers_for_tutor(message, person)
            return
        elif not (len(t) == 5 and ":" in text and text.count("-") == 2 and "dz" in text and "ans" in text):
            msg = bot.send_message(person.user_id, text="Данные введены неверно")
            
            navigation(msg, person)
            return
        try:
            info = {"student_name": t[0] + " " + t[1], "dz": int(t[2].split("-")[-1]), "ans": int(t[3].split("-")[-1][:-1]), "cur_ans": t[-1]}
        except Exception:
            msg = bot.send_message(person.user_id, text="Данные введены неверно")
            
            navigation(message, person)
            return

        update_answers_for_dz(info["student_name"], info["dz"], info["ans"], info["cur_ans"])
        msg = bot.send_message(person.user_id, text="Успешно исправлено")
        
        navigation(message, person)

    def update_dz(message: Message, person: Tutor, is_delete):
        text = message.text
        t = text.split()
        if text == "/my_students":
            get_list_students(message, person)
            return
        elif text == "/get_dz":
            get_dz_for_tutor(message, person)
            return
        elif not (len(t) == 3 and "dz-" in text):
            msg = bot.send_message(person.user_id, text="Данные введены неверно")
            
            navigation(msg, person)
            return
        try:
            info = {"student_name": t[0] + " " + t[1], "dz": int(t[2].split("-")[-1])}
        except Exception:
            msg = bot.send_message(person.user_id, text="Данные введены неверно")
            
            navigation(message, person)
            return
        if is_delete:
            path = select_path_to_file(info["dz"], info["student_name"])
            os.remove(path)
            delete_dz(info["dz"], info["student_name"])
            msg = bot.send_message(person.user_id, text="Удаление прошло успешно")
            
            navigation(message, person)
        else:
            msg = bot.send_message(person.user_id, text="Прикрепите файл, на который необходимо заменить прошлый файл")
            
            bot.register_next_step_handler(msg, get_path, person, info)

    def get_path(message: Message, person: Tutor, info: dict):
        try:
            file_info = bot.get_file(message.document.file_id)
            file = Files(bot.download_file(file_info.file_path), file_info.file_path.split('.')[-1])
            file.name = select_path_to_file(info["dz"], info["student_name"]).split("/")[-1][:-4]
            file.convert_to_pdf()
        except AttributeError:
            bot.send_message(person.user_id, text="Ошибка чтения файла. Необходимо прикрепить файл.")
            navigation(message, person)
            return

        bot.send_message(person.user_id, text="Файл обновлен успешно")
        bot.send_message()
        navigation(message, person)

    if person is None:
        person = init_person(message)
    if isinstance(person, Student):
        navigation(message, person)
        return
    get_info(person)

@bot.message_handler(commands=["get_dz"])
def get_dz_for_tutor(message: Message, person: Tutor | None = None, isStuff=False):
    def define_student():
        nonlocal person
        if person is None:
            person = init_person(message)
        if isinstance(person, Student):
            bot.send_message(person.user_id, text="Ошибка доступа")
            
            return
        students = person.get_students()
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        students_dict = dict()
        for student in students:
            button = KeyboardButton(text=student.name)
            students_dict[student.name] = student.user_id
            keyboard.add(button)
        back = KeyboardButton(text="Назад")
        keyboard.add(back)
        msg = bot.send_message(person.user_id, text="Выбор ученика", reply_markup=keyboard)
        
        bot.register_next_step_handler(msg, define_dz, students_dict)

    def define_dz(message: Message, students_dict: dict):
        text = message.text
        if text == "Назад":
            navigation(message, person)
            return
        elif text not in students_dict.keys():
            msg = bot.send_message(person.user_id,
                             text="Введено неверное имя ученика. Попробуйте просто нажать на клавиатуру")
            
            return
        student = Student(int(students_dict[text]))
        counter = count_dz_for_student(student.user_id)
        msg = bot.send_message(person.user_id, text=f"выберите номер домашнего задания, который хотите получить. Всего у ученика {counter} дз.")
        
        if not isStuff:
            bot.register_next_step_handler(msg, get_file, student, counter)
        else:
            bot.register_next_step_handler(msg, get_answers_for_tutor, isStuff=True, student=student)

    def get_file(message: Message, student, counter):
        text = message.text
        keyboard = ReplyKeyboardMarkup()
        keyboard.add(KeyboardButton(text="Назад"))
        try:
            number = int(text)
        except Exception:
            navigation(message, person)
            return
        if 0 < number <= counter:
            path_to_file = select_dz_by_number(number, student.user_id)[0]['path_to_file']
            file_name = f"dz-{number}.pdf"
            try:
                file = open(path_to_file, "rb")
                msg = bot.send_message(person.user_id, text=f"Домашняя работа для {student.name}")
                
                msg = bot.send_document(person.user_id, document=file, visible_file_name=file_name, reply_markup=keyboard)
                
                bot.register_next_step_handler(msg, define_person_action, person)
            except FileNotFoundError as ex:
                print(ex)
                msg = bot.send_message(person.user_id, text="Ошибка")
                
                navigation(message, person)
                return
    define_student()


@bot.message_handler(commands=["get_answers"])
def get_answers_for_tutor(message: Message, person=None, isStuff=False, student=None):
    def define_number_dz(person):
        if person is None:
            person = init_person(message)
        if not isinstance(person, Tutor):
            msg = bot.send_message(person.user_id, text="Ошибка доступа")
            
            navigation(message, person)
            return
        get_dz_for_tutor(message, person, isStuff=True)

    def get_answers(message, person):
        if person is None:
            person = init_person(message)
        text = message.text
        keyboard = ReplyKeyboardMarkup()
        keyboard.add(KeyboardButton(text="Назад"))
        counter = count_dz_for_student(student.user_id)
        try:
            number = int(text)
        except ValueError:
            navigation(message, person)
            return
        if 0 < number <= counter:
            answers ="\n".join(list(map(lambda x: ': '.join((str(x[0]), x[1])), select_answers(number, student.user_id).items())))

        msg = bot.send_message(person.user_id, text=f"Ответы для {student.name} по домашке dz-{number}:\n{answers}")
        
        navigation(message, person)
    if not isStuff:
        define_number_dz(person)
    else:
        get_answers(message, person)


@bot.message_handler(commands=["my_students"])
def get_list_students(message: Message, person: Tutor | None=None):
    if person is None:
        person = init_person(message)
    text = ""
    for student in person.get_students():
        text += f"{student.name}\n"
    if not text:
        msg = bot.send_message(person.user_id, text="У вас еще нет учеников")
        
    else:
        msg = bot.send_message(person.user_id, text=text)
        
    navigation(message, person)


def init_person(message) -> Tutor | Student:
    user_id = message.from_user.id
    if select_person(user_id, "tutor"):
        person = Tutor(user_id)
    else:
        person = Student(user_id)

    if not person.isval and isinstance(person, Student):
        registration(message, person)
    return person


def registration(message: Message, person: Student, has_make_register=None):
    if has_make_register is None:
        msg = bot.send_message(person.user_id,
                               text="<strong><i>Регистрация</i></strong> \n\n\n Введите на первой строке ваше имя и фамилию, а на второй строке имя репетитора. \n\n <b>Например: </b> <i>Иван Иванов\nМатвей</i>",
                               parse_mode='HTML')
        
        bot.register_next_step_handler(msg, registration, person, False)
    elif not has_make_register:
        data = message.text.split("\n")
        if len(data) != 2 or len(data[0].split()) != 2:
            msg = bot.send_message(person.user_id,
                                   text="Данные введены неверно. Сообщение должно состоять из двух слов: Имя и Фамилия, разделенные пробелом")
            
            bot.register_next_step_handler(msg, registration, person, False)
        else:
            fio = data[0].split()
            tutor = data[1].lower()
            if tutor not in list(map(lambda x: x["name"][:-2].lower(), select_all_persons("tutor"))):
                msg = bot.send_message(person.user_id,
                                       text="Данные введены неверно. Сообщение должно состоять из двух слов: Имя и Фамилия, разделенные пробелом")
                
                bot.register_next_step_handler(msg, registration, person, False)

            student_name = f"{fio[0]} {fio[1][0]}".title()
            person.register(message.from_user.username, tutor, student_name)
            registration(message, person, True)
    elif has_make_register:
        msg = bot.send_message(person.user_id,
                               text="Вы успешно зарегистрированы!")
        msg = bot.send_message(person.user_id, text=f'Этот бот создан для автоматической рассылки и проверки '
                                                    f'домашней работы. \n\n Здесь ты будешь получать уведомления при '
                                                    f'поступлении новой домашки! \n \n После выполнения заданий, тебе '
                                                    f'необходимо отправить их на проверку также через этого бота. \n\n'
                                                    f'Для навигации введи команду: /nav\n', is_deleting=False)
        bot.pin_chat_message(person.user_id, msg.chat.id)
        navigation_for_student(msg, person)


def navigation_for_student(message: Message, person: Student | None = None):
    if person is None:
        person = init_person(message)

    keyboard = tb.types.ReplyKeyboardMarkup(resize_keyboard=True)
    button1 = KeyboardButton(text='Последнее дз')
    button2 = KeyboardButton(text='Получить дз по номеру')
    button3 = KeyboardButton(text='Проверка дз')
    keyboard.add(button1)
    keyboard.add(button2)
    keyboard.add(button3)
    msg = bot.send_message(person.user_id, text=f'Выбери свое дальнейшее действие:', reply_markup=keyboard)
    bot.register_next_step_handler(msg, define_person_action, person)


def navigation_for_tutor(message: Message, person: Tutor | None | Student = None):
    if person is None:
        person = init_person(message)
    if isinstance(person, Student):
        msg = bot.send_message(person.user_id, text="Ошибка допуска")
        
        navigation_for_student(message, person)

    keyboard = tb.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    button1 = KeyboardButton(text="Загрузка дз")
    button2 = KeyboardButton(text="Просмотр дз")
    button3 = KeyboardButton(text="Просмотр ответов")
    button4 = KeyboardButton(text="Исправить ошибку")
    keyboard.add(button1, button2, button3, button4)
    bot.send_message(person.user_id, text="Выбери дейтсвие:", reply_markup=keyboard)
    bot.register_next_step_handler(message, define_person_action,  person)


def define_person_action(message: Message, person: Student | Tutor):
    msg_text = message.text
    match msg_text:
        case 'Последнее дз':
            get_last_dz(message, person) if isinstance(person, Student) else None
        case 'Получить дз по номеру':
            get_dz_by_number(person) if isinstance(person, Student) else None
        case 'Проверка дз':
            check_dz(person) if isinstance(person, Student) else None
        case 'Загрузка дз':
            download_task(message, person) if isinstance(person, Tutor) else None
        case 'Просмотр дз':
            get_dz_for_tutor(message, person) if isinstance(person, Tutor) else None
        case 'Просмотр ответов':
            get_answers_for_tutor(message, person) if isinstance(person, Tutor) else None
        case 'Исправить ошибку':
            navigation_with_mistakes(message, person) if isinstance(person, Tutor) else None
        case 'Назад':
            navigation(message, person)


def download_task(message: Message, person: Tutor):
    def choice_student():
        keyboard = tb.types.ReplyKeyboardMarkup(resize_keyboard=True)
        students = person.get_students()
        students_dict = dict()
        for student in students:
            button = KeyboardButton(text=student.name)
            keyboard.add(button)
            students_dict[student.name] = student.user_id
        back_nav = KeyboardButton(text="Назад")
        keyboard.add(back_nav)
        msg = bot.send_message(person.user_id, text="Выбери ученика:", reply_markup=keyboard)
        
        bot.register_next_step_handler(msg, define_student, students_dict)

    def define_student(message: Message, students_dict: dict):
        text = message.text
        if text == "Назад":
            navigation(message, person)
            return
        elif text not in students_dict.keys():
            msg = bot.send_message(person.user_id, text="Введено неверное имя ученика. Попробуйте просто нажать на клавиатуру")
            
            return
        student = Student(int(students_dict[text]))
        msg = bot.send_message(person.user_id, text="Прикрепи файл с дз в формате pdf, doc, docx")
        
        bot.register_next_step_handler(msg, define_file,  student)

    def define_file(message: Message, student: Student):
        try:
            file_info = bot.get_file(message.document.file_id)
            file = Files(bot.download_file(file_info.file_path), file_info.file_path.split('.')[-1])
            file.name = student.name
            file.convert_to_pdf()
        except AttributeError:
            bot.send_message(person.user_id, text="Ошибка чтения файла. Необходимо прикрепить файл.")
            navigation(message, person)
            return

        add_new_dz(student.user_id, file.get_src())
        msg = bot.send_message(person.user_id, text='Супер! Домашняя работа загрузилась и уже доставлена ученику! Пора загрузить ответы. \n\n Ответы вводятся <b>одной</b> строкой, разделяются <b>одним</b> пробелом. Количество ответов должно совпадать с количеством заданий!', parse_mode='HTML')
        
        get_dz(msg, student, select_last_dz_id(student.user_id))
        bot.register_next_step_handler(msg, define_answers, student)

    def define_answers(message: Message, student: Student):
        answers = message.text.split()
        dz_id = select_last_dz_id(student.user_id)
        number_task = 1

        for answer in answers:
            add_answer_for_dz(dz_id, student.user_id, number_task, answer)
            number_task += 1

        msg = bot.send_message(person.user_id, text=f"Ответы в количестве {number_task - 1} загружены. При обнаружении ошибки использовать команду: /mistake")
        
    choice_student()

@bot.message_handler(commands=["get_last_dz"])
def get_last_dz(message: Message, person: Student | None = None):
    if person is None:
        person = init_person(message)
    elif isinstance(person, Tutor):
        navigation(message, person)
        return
    number = select_last_dz_id(person.user_id)
    if number:
        get_dz(message, person, number)
    else:
        bot.send_message(person.user_id, text="У вас еще нет домашек")


def get_dz_by_number(person: Student | None = None):
    def define_number():
        counter = count_dz_for_student(person.user_id)
        msg = bot.send_message(person.user_id, text=f"Введите номер дз, которое хотите получить."
                                          f"Всего домашних работ у вас: {counter}")
        
        bot.register_next_step_handler(msg, get_number)

    def get_number(message: Message):
        text = message.text
        try:
            number = int(text)
        except Exception:
            msg = bot.send_message(person.user_id, text="Неверено введен номер дз.")
            
            navigation(message, person)
            return
        if 0 < number <= count_dz_for_student(person.user_id):
            get_dz(message, person, number)
        else:
            msg = bot.send_message(person.user_id, text="Домашней работы с таким номером не существует")
            
            navigation(message, person)
    define_number()

def get_dz(message: Message, person: Student, number: int):
    file_name = f"dz-{number}.pdf"
    path = select_path_to_file(number, person.name)
    bot.send_message(person.user_id, text="Домашнее задание:", is_deleting=False)
    try:
        file = open(path, "rb")
        bot.send_document(person.user_id, document=file, visible_file_name=file_name, is_deleting=False)
    except FileNotFoundError as ex:
        print(ex)
        msg = bot.send_message(person.user_id, text="Ошибка")
        
    finally:
        navigation(message, person)

def check_dz(person: Student | None = None):
    def define_dz():
        msg = bot.send_message(person.user_id, text="Введите номер домашней работы, на которую вы хотите дать ответ")
        
        bot.register_next_step_handler(msg, define_answer)

    def define_answer(message: Message):
        text = message.text
        try:
            dz_id = int(text)
        except ValueError:
            msg = bot.send_message(person.user_id, text="Введено неверное значение. "
                                                  "Необходимо вводить только "
                                                  "одно число - номер дз")
            
            navigation(message, person)
            return
        if not 0 < dz_id <= count_dz_for_student(person.user_id):
            msg = bot.send_message(person.user_id, text="Домашней работы с таким номером не существует")
            
            navigation(message, person)
            return
        if select_has_answer_in_dz(dz_id, person.user_id):
            msg = bot.send_message(person.user_id, text="Ответ для домашней работы уже был дан. Результаты изменить нельзя")
            
            navigation(message, person)
            return
        msg = bot.send_message(person.user_id, text=f"Вводите ответы для dz-{dz_id}")
        
        bot.register_next_step_handler(msg, check_answers, dz_id)

    def check_answers(message: Message, dz_id: int):
        answers = message.text.split()
        correct_answers = select_answers(dz_id, person.user_id)
        if len(answers) != len(correct_answers):
            msg = bot.send_message(person.user_id, text="Введено неверное количество ответов")
            
            navigation(message, person)
        number_of_correct_answer = sum(list(correct_answers.values())[i] == answers[i] for i in range(len(correct_answers)))
        update_answer_in_answers(dz_id, person.user_id, answers)
        change_has_answer_in_dz(dz_id, person.user_id)
        bot.send_message(person.user_id, text=f"Для домашней работы dz-{dz_id} введено {number_of_correct_answer} из {len(answers)} верных ответов. Результаты отправлены преподавателю.", is_deleting=False)
        tutor = person.get_tutor()

        result = ""
        for i in range(len(answers)):
            result += f"{i + 1}) {correct_answers[i + 1]} / {answers[i]}\n"
        bot.send_message(tutor.user_id, text=f"{person.name} выполнил домашнюю работу: dz-{dz_id}. Результат: {number_of_correct_answer} из {len(answers)}.\n\ {result}", is_deleting=False)
        navigation(message, person)

    define_dz()
    pass

if __name__ == '__main__':
    bot.polling()
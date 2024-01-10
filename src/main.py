import pathlib

import telebot as tb
import os
from datetime import datetime
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from telebot.types import Message
from config import config
from roles import Student, Tutor
from actions import Action
from database.requests import *

bot = tb.TeleBot(token=config.TOKEN)

@bot.message_handler(commands=["start"])
def welcome(message: Message):
    user_id = message.chat.id
    bot.send_message(user_id, text="Привет!")

    person = init_person(message)

    if person.isval:
        navigation(message, person)
        return

    if isinstance(person, Tutor):
        bot.send_message(user_id, text="Вы не репетитор!")
    elif isinstance(person, Student):
        registration(message, person)
    else:
        bot.send_message(user_id, text="Какая - то ошибка")
        raise TypeError("Person is Null")

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

    def get_info(message: Message, person: Tutor):
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
            bot.send_message(person.user_id, text="Если вы ввели не правильно один из ответов"
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
        elif text == "Прикрепить новый файл":
            bot.send_message(person.user_id, text="Для данного действия вам необходимо:\n"
                                                  "1) выбрать ученика (при желании можно "
                                                  "посмотреть при помощи команды /my_students\n"
                                                  "2) выбрать номер домашней работы"
                                                  " (при желнии можно просмотреть "
                                                  "ее содержимое командой: /get_dz\n")
            msg = bot.send_message(person.user_id, text="Введите одной строкой данную информацию.\n"
                                                  "Например: <b>Иван И dz-1</b>\n"
                                                  "Здесь <i>'Иван И'</i> - имя и фамилия ученика;\n"
                                                  "<i>'dz-1'</i> - номер домашней работы/", parse_mode="HTML")
            bot.register_next_step_handler(msg, update_dz, person)
        elif text == "Удалить домашнюю работу":
            pass #todo
    def update_answer(message: Message, person: Tutor):
        text = message.text
        t = text.split()
        if not (len(t) == 5 and ":" in text and text.count("-") == 2 and "dz" in text and "ans" in text):
            msg = bot.send_message(person.user_id, text="Данные введены неверно1")
            navigation(msg, person)
            return
        try:
            info = {"student_name": t[0] + " " + t[1], "dz": int(t[2].split("-")[-1]), "ans": int(t[3].split("-")[-1][:-1]), "cur_ans": t[-1]}
        except Exception:
            bot.send_message(person.user_id, text="Данные введены неверно2")
            navigation(message, person)
            return

        update_answers_for_dz(info["student_name"], info["dz"], info["ans"], info["cur_ans"])
        bot.send_message(person.user_id, text="Успешно исправлено")
        navigation(message, person)
    def update_dz(message: Message, person: Tutor):
        text = message.text
        t = text.split()
        if not (len(t) == 3 and "dz-" in text):
            msg = bot.send_message(person.user_id, text="Данные введены неверно")
            navigation(msg, person)
            return
        try:
            info = {"student_name": t[0] + " " + t[1], "dz": int(t[2].split("-")[-1])}
        except Exception:
            bot.send_message(person.user_id, text="Ошибка чтения файла. Необходимо прикрепить файл.")
            navigation(message, person)
            return
        msg = bot.send_message(person.user_id, text="Прикрепите файл, на который необходимо заменить прошлый файл")
        bot.register_next_step_handler(msg, get_path, person, info)
    def get_path(message: Message, person: Tutor, info: dict):
        try:
            file_info = bot.get_file(message.document.file_id)
            file = bot.download_file(file_info.file_path)
        except AttributeError:
            bot.send_message(person.user_id, text="Ошибка чтения файла. Необходимо прикрепить файл.")
            navigation(message, person)
            return
        src = os.path.abspath('../files/')
        os.chdir(src)
        file_name = select_path_to_file(info["dz"], info["student_name"])
        os.remove(file_name)
        file_name = file_name.split("/")[-1][:-4]
        with open(file_name, 'wb') as new_file:
            new_file.write(file)
            pdf_file = file_name + ".pdf"
        os.rename(file_name, pdf_file)
        bot.send_message(person.user_id, text="Файл обновлен успешно")
        navigation(message, person)


    if person is None:
        person = init_person(message)
    if isinstance(person, Student):
        navigation(message, person)
        return
    get_info(message, person)
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
        new_msg = bot.send_message(person.user_id, text="Выбор ученика", reply_markup=keyboard)
        bot.register_next_step_handler(new_msg, define_dz, students_dict)
    def define_dz(message: Message, students_dict: dict):
        text = message.text
        if text == "Назад":
            navigation(message, person)
            return
        elif text not in students_dict.keys():
            bot.send_message(person.user_id,
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
                bot.send_message(person.user_id, text=f"Домашняя работа для {student.name}")
                msg = bot.send_document(person.user_id, file, visible_file_name=file_name, reply_markup=keyboard)
                bot.register_next_step_handler(msg, define_person_action, person)
            except FileNotFoundError as ex:
                print(ex)
                return
    define_student()

@bot.message_handler(commands=["get_answers"])
def get_answers_for_tutor(message: Message, person=None, isStuff=False, student=None):
    def define_number_dz(person):
        if person is None:
            person = init_person(message)
        if not isinstance(person, Tutor):
            bot.send_message(person.user_id, text="Ошибка доступа")
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
            answers = "\n".join(select_answers(number, student.user_id))

        bot.send_message(person.user_id, text=f"Ответы для {student.name} по домашке dz-{number}:\n{answers}")

    if not isStuff:
        define_number_dz(person)
    else:
        get_answers(message, person)

@bot.message_handler(commands=["my_students"])
def get_list_students(message: Message, person: Tutor | None=None):
    if person is None:
        person = init_person(message)
    msg = ""
    for student in person.get_students():
        msg += f"{student.name}\n"
    bot.send_message(person.user_id, text=msg)
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
            if tutor not in map(lambda x: x["name"], select_all_persons("tutor")):
                msg = bot.send_message(person.user_id,
                                       text="Данные введены неверно. Сообщение должно состоять из двух слов: Имя и Фамилия, разделенные пробелом")
                bot.register_next_step_handler(msg, registration, person, False)

            student_name = f"{fio[0]} {fio[1][0]}".title()
            person.register(message.from_user.username, tutor, student_name)
            registration(message, person, True)
    elif has_make_register:
        msg = bot.send_message(person.user_id,
                               text="Вы успешно зарегистрированы!")
        navigation_for_student(msg, person)

def navigation_for_student(message: Message, person: Student | None = None):
    if person is None:
        person = init_person(message)

    keyboard = tb.types.ReplyKeyboardMarkup(resize_keyboard=True)
    button1 = KeyboardButton(text='Последнее дз')
    button2 = KeyboardButton(text='Полный список дз')
    button3 = KeyboardButton(text='Проверка дз')
    button4 = KeyboardButton(text='Инструкция по отправке дз')
    keyboard.add(button1)
    keyboard.add(button2)
    keyboard.add(button3)
    keyboard.add(button4)
    bot.send_message(message.chat.id, text=str(f'Этот бот создан для автоматической рассылки и проверки '
                                               f'домашней работы. \n\n Здесь ты будешь получать уведомления при '
                                               f'поступлении новой домашки! \n \n После выполнения заданий, тебе '
                                               f'необходимо отправить их на проверку также через этого бота. \n\n '
                                               f'Выбери свое дальнейшее действие:'), reply_markup=keyboard)

def navigation_for_tutor(message: Message, person: Tutor | None | Student = None):
    if person is None:
        person = init_person(message)
    if isinstance(person, Student):
        bot.send_message(person.user_id, text="Ошибка допуска")
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
    action = Action(person)
    match msg_text:
        case 'Последнее дз':
            action.get_last_dz() if isinstance(person, Student) else None
        case 'Полный список дз':
            action.get_all_dz() if isinstance(person, Student) else None
        case 'Проверка дз':
            action.check_dz() if isinstance(person, Student) else None
        case 'Инструкция по отправке дз':
            action.get_manual() if isinstance(person, Student) else None
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
    def choice_student(message: Message):
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
            bot.send_message(person.user_id, text="Введено неверное имя ученика. Попробуйте просто нажать на клавиатуру")
            return
        student = Student(int(students_dict[text]))
        msg = bot.send_message(person.user_id, text="Прикрепи файл с дз в формате pdf, doc, docx")
        bot.register_next_step_handler(msg, define_file,  student)

    def define_file(message: Message, student: Student):
        try:
            file_info = bot.get_file(message.document.file_id)
            file = bot.download_file(file_info.file_path)
        except AttributeError:
            bot.send_message(person.user_id, text="Ошибка чтения файла. Необходимо прикрепить файл.")
            navigation(message, person)
            return

        now = datetime.now()
        file_name = student.name + "_{}.{}.{}_{}.{}".format(now.day, now.month, now.year, now.hour, now.minute)
        src = os.path.abspath('../files/')
        os.chdir(src)

        with open(file_name, 'wb') as new_file:
            new_file.write(file)
            pdf_file = file_name + ".pdf"

        os.rename(file_name, pdf_file)
        add_new_dz(student.user_id, src.replace('\\', '/') + "/" + pdf_file)
        message = bot.send_message(person.user_id, text='Супер! Домашняя работа загрузилась и уже доставлена ученику! Пора загрузить ответы. \n\n Ответы вводятся <b>одной</b> строкой, разделяются <b>одним</b> пробелом. Количество ответов должно совпадать с количеством заданий!', parse_mode='HTML')
        bot.register_next_step_handler(message, define_answers, student)
    def define_answers(message: Message, student: Student):
        answers = message.text.split()
        dz_id = select_last_dz_id(student.user_id)[0]["id"]
        number_task = 1

        for answer in answers:
            add_answer_for_dz(dz_id, student.user_id, number_task, answer)
            number_task += 1

        bot.send_message(person.user_id, text=f"Ответы в количестве {number_task - 1} загружены. При обнаружении ошибки использовать команду: /mistake")
    choice_student(message)


if __name__ == '__main__':
    bot.polling()
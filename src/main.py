import time
import types
from abc import ABC, abstractmethod
import telebot as tb
import os
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, Message, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from config.properties import TelebotProperties, CommandsProperties
from files import File_faсtory, HomeworkDocument, Jpg_file, Callback_data
from roles import Student, Tutor
from database import requests
import threading
import json

class Deleting_telebot(tb.TeleBot):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queue_menu = {}
        self.callback_list = list()

    def send_message(self, *args, is_deleting: bool = True, is_menu = False, **kwargs) -> Message:
        msg = super().send_message(*args, **kwargs)
        if is_menu:
            if msg.chat.id in self.queue_menu:
                self.queue_menu[msg.chat.id].append(msg)
                del_msg = self.queue_menu[msg.chat.id].pop(0)
                thr = threading.Thread(target=self.delete_message_with_delay, args=(del_msg,))
                thr.start()
            else:
                self.queue_menu[msg.chat.id] = [msg]
        elif is_deleting:
            thr = threading.Thread(target=self.delete_message_with_delay, args=(msg,))
            thr.start()
        return msg

    def send_document(self, *args, is_deleting: bool = True, **kwargs) -> Message:
        msg = super().send_document(*args, **kwargs)
        if is_deleting:
            thr = threading.Thread(target=self.delete_message_with_delay, args=(msg,))
            thr.start()
        return msg

    def process_new_messages(self, new_messages):
        thr = threading.Thread(target=self.delete_message_with_delay, args=(new_messages[0],))
        thr.start()
        super().process_new_messages(new_messages)

    def delete_message_with_delay(self, message):
        time.sleep(int(TelebotProperties().get_message_delay()))
        self.delete_message(message.chat.id, message.id)

    def add_callback(self, callback: Callback_data):
        self.callback_list.append(callback)

    def get_callback(self, index: int):
        if index < len(self.callback_list):
            return self.callback_list.pop(index)

bot = Deleting_telebot(token=TelebotProperties().get_token())
cmd = CommandsProperties()

class permission_to_receive_photo:
    is_allowed = False

    @classmethod
    def change_permission(cls, value: bool = None):
        if value is None:
            cls.is_allowed = not cls.is_allowed
        else:
            cls.is_allowed = value

    @classmethod
    def get_permission(cls, *args, **kwargs):
        return cls.is_allowed


@bot.message_handler(commands=[cmd.get_start()])
def welcome(message: Message):
    user_id = message.chat.id
    person = init_person(message)

    if person.isval:
        bot.send_message(user_id, text="Привет!")
        navigation(message, person)
        return


def init_person(message) -> Tutor | Student:
    user_id = message.from_user.id
    if requests.select_person(user_id, "tutor"):
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
                                   text="Данные введены неверно. Сообщение должно состоять из Имени и Фамилии, разделенные пробелом, а на второй строке имя преподавателя.")

            bot.register_next_step_handler(msg, registration, person, False)
        else:
            fio = data[0].split()
            tutor = data[1].lower()
            if tutor not in map(lambda x: x["name"][:-2].lower(), requests.select_all_persons("tutor")):
                msg = bot.send_message(person.user_id,
                                       text="Данные введены неверно. Имя преподавателя не найдено в базе. Попробуй еще раз!")

                bot.register_next_step_handler(msg, registration, person, False)

            student_name = f"{fio[0]} {fio[1][0]}".title()
            person.register(message.from_user.username, tutor, student_name)
            registration(message, person, True)
    elif has_make_register:
        bot.send_message(person.user_id,
                         text="Вы успешно зарегистрированы!")
        msg = bot.send_message(person.user_id, text=f'Этот бот создан для автоматической рассылки и проверки '
                                                    f'домашней работы. \n\n Здесь ты будешь получать уведомления при '
                                                    f'поступлении новой домашки! \n \n После выполнения заданий, тебе '
                                                    f'необходимо отправить их на проверку также через этого бота. \n\n'
                                                    f'Для навигации нажми на: /nav\n', is_deleting=False)
        bot.pin_chat_message(person.user_id, msg.id)
        navigation(msg, person)


@bot.message_handler(commands=[cmd.get_navigation()])
def navigation(message: Message, person: Student | None | Tutor = None):
    if person is None:
        person = init_person(message)

    if isinstance(person, Tutor):
        navigation_for_tutor(person)
    elif isinstance(person, Student):
        navigation_for_student(person)


def navigation_for_tutor(person: Tutor):
    keyboard = tb.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    button1 = KeyboardButton(text="Загрузка дз")
    button2 = KeyboardButton(text="Просмотр дз")
    button3 = KeyboardButton(text="Просмотр ответов")
    button4 = KeyboardButton(text="Исправить ошибку")
    keyboard.add(button1, button2, button3, button4)

    msg = bot.send_message(person.user_id, text="Выбери действие:", reply_markup=keyboard, is_menu=True)
    bot.register_next_step_handler(msg, define_person_action, person)


def navigation_for_student(person: Student):
    keyboard = tb.types.ReplyKeyboardMarkup(resize_keyboard=True)
    button1 = KeyboardButton(text='Последнее дз')
    button2 = KeyboardButton(text='Получить дз по номеру')
    button3 = KeyboardButton(text='Проверка дз')
    keyboard.add(button1)
    keyboard.add(button2)
    keyboard.add(button3)

    msg = bot.send_message(person.user_id, text=f'Выбери свое дальнейшее действие:', reply_markup=keyboard, is_menu=True)
    bot.register_next_step_handler(msg, define_person_action, person)


def define_person_action(message: Message, person: Student | Tutor):
    msg_text = message.text
    match msg_text:
        case 'Последнее дз':
            get_last_dz(message, person) if isinstance(person, Student) else None
        case 'Получить дз по номеру':
            get_dz_by_number(person) if isinstance(person, Student) else None
        case 'Проверка дз':
            Checker_dz(person).check_dz() if isinstance(person, Student) else None
        case 'Загрузка дз':
            if isinstance(person, Tutor):
                Downloader_task(message, person).download_task()
        case 'Просмотр дз':
            get_dz_for_tutor(message, person) if isinstance(person, Tutor) else None
        case 'Просмотр ответов':
            get_answers_for_tutor(message, person) if isinstance(person, Tutor) else None
        case 'Исправить ошибку':
            navigation_for_mistakes(message, person) if isinstance(person, Tutor) else None
        case 'Назад':
            navigation(message, person)


@bot.message_handler(commands=[cmd.get_mistake()])
def navigation_for_mistakes(message: Message, person: Tutor | None = None):
    if person is None:
        person = init_person(message)
    Navigator_for_mistakes(person)

class Navigator_for_mistakes:
    def __init__(self, person: Tutor):
        if isinstance(person, Student):
            msg = bot.send_message(person.user_id, text="Ошибка доступа")
            navigation(msg, person)
            return
        self.person = person
        self.get_info()
    def get_info(self):
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        button1 = KeyboardButton(text="Изменить ответ")
        button2 = KeyboardButton(text="Прикрепить новый файл")
        button3 = KeyboardButton(text="Удалить домашнюю работу")
        button4 = KeyboardButton(text="Назад")
        keyboard.add(button1, button2, button3, button4)
        msg = bot.send_message(self.person.user_id, text="Выберите действие, которое необходимо выполнить:",
                               reply_markup=keyboard)

        bot.register_next_step_handler(msg, self.define_mistake)

    def define_mistake(self, message: Message):
        text = message.text
        if text == "Назад":
            navigation(message, self.person)
        elif text == "Изменить ответ":
            bot.send_message(self.person.user_id, text="Если вы ввели не правильно один из ответов"
                                                        " в домашней работе вам следует:\n"
                                                        " 1) выбрать ученика. При желании можно "
                                                        "посмотреть при помощи команды /my_students\n"
                                                        " 2) выбрать номер домашней работы."
                                                        " При желнии можно просмотреть "
                                                        "ее содержимое командой: /get_dz\n "
                                                        "3) Выбрать номер ответа, который "
                                                        "следует отредактировать. При желании "
                                                        "можно просмотреть все правильные ответы "
                                                        "для дз при помощи команды: /get_answer", reply_markup=ReplyKeyboardRemove())

            msg = bot.send_message(self.person.user_id, text="Введите одной строкой данную информацию.\n"
                                                        "Например: <strong>Иван И dz-1 ans-1: 123</strong>\n"
                                                        "Здесь <i>'Иван И'</i> - имя и фамилия ученика;\n"
                                                        "<i>'dz-1'</i> - номер домашней работы;\n"
                                                        "<i>'ans-1'</i> - номер ответа;\n"
                                                        "<i>'123'</i> - правильный ответ.", parse_mode="HTML")

            bot.register_next_step_handler(msg, self.update_answer)
        elif text in ("Прикрепить новый файл", "Удалить домашнюю работу"):
            bot.send_message(self.person.user_id, text="Для данного действия вам необходимо:\n"
                                                        "1) выбрать ученика (при желании можно "
                                                        "посмотреть при помощи команды /my_students\n"
                                                        "2) выбрать номер домашней работы"
                                                        " (при желнии можно просмотреть "
                                                        "ее содержимое командой: /get_dz\n")

            msg = bot.send_message(self.person.user_id, text="Введите одной строкой данную информацию.\n"
                                                        "Например: <b>Иван И dz-1</b>\n"
                                                        "Здесь <i>'Иван И'</i> - имя и фамилия ученика;\n"
                                                        "<i>'dz-1'</i> - номер домашней работы/", parse_mode="HTML")

            bot.register_next_step_handler(msg, self.update_dz, is_delete=(text == "Удалить домашнюю работу"))

    def update_answer(self, message: Message):
        text = message.text
        t = text.split()
        if not (len(t) == 5 and ":" in text and text.count("-") == 2 and "dz" in text and "ans" in text):
            msg = bot.send_message(self.person.user_id, text="Данные введены неверно")
            navigation(msg, self.person)
            return
        try:
            info = {"student_name": t[0] + " " + t[1], "dz": int(t[2].split("-")[-1]),
                    "ans": int(t[3].split("-")[-1][:-1]), "cur_ans": t[-1]}
        except Exception:
            bot.send_message(self.person.user_id, text="Данные введены неверно")
            navigation(message, self.person)
            return

        requests.update_answers_for_dz(info["student_name"], info["dz"], info["ans"], info["cur_ans"])
        msg = bot.send_message(self.person.user_id, text="Успешно исправлено")

        navigation(msg, self.person)

    def update_dz(self, message: Message, is_delete):
        text = message.text
        t = text.split()
        if text == "/my_students":
            get_list_students(message, self.person)
            return
        elif text == "/get_dz":
            get_dz_for_tutor(message, self.person)
            return
        elif not (len(t) == 3 and "dz-" in text):
            msg = bot.send_message(self.person.user_id, text="Данные введены неверно")

            navigation(msg, self.person)
            return
        try:
            self.info = {"student_name": t[0] + " " + t[1], "dz": int(t[2].split("-")[-1])}
        except Exception:
            bot.send_message(self.person.user_id, text="Данные введены неверно")
            navigation(message, self.person)
            return

        if is_delete:
            path = requests.select_path_to_file(self.info["dz"], self.info["student_name"])
            os.remove(path)
            requests.delete_dz(self.info["dz"], self.info["student_name"])
            msg = bot.send_message(self.person.user_id, text="Удаление прошло успешно")

            navigation(msg, self.person)
        else:
            msg = bot.send_message(self.person.user_id, text="Прикрепите файл, на который необходимо заменить прошлый файл")

            bot.register_next_step_handler(msg, self.get_path)

    def get_path(self, message: Message):
        try:
            file_info = bot.get_file(message.document.file_id)
            file = File_faсtory(bot.download_file(file_info.file_path), file_info.file_path.split('.')[-1])
            file.name = requests.select_path_to_file(self.info["dz"], self.info["student_name"]).split("/")[-1][:-4]
            file.convert_to_pdf()
        except AttributeError:
            bot.send_message(self.person.user_id, text="Ошибка чтения файла. Необходимо прикрепить файл.")
            navigation(message, self.person)
            return

        bot.send_message(self.person.user_id, text="Файл обновлен успешно")
        bot.send_message()
        navigation(message, self.person)

@bot.message_handler(commands=[cmd.get_dz_for_tutor()])
def get_dz_for_tutor(message: Message, person: Tutor | None = None):
    if person is None:
        person = init_person(message)
    Sender_dz(person=person, recipient=person).start()


@bot.message_handler(commands=[cmd.get_answers_for_tutor()])
def get_answers_for_tutor(message: Message, person: Tutor | None = None):
    if person is None:
        person = init_person(message)

    if not isinstance(person, Tutor):
        bot.send_message(person.user_id, text="Ошибка доступа")
        navigation(message, person)
        return

    Sender_answer(person=person, recipient=person).start()


@bot.message_handler(commands=[cmd.get_students_list()])
def get_list_students(message: Message, person: Tutor | None = None):
    if person is None:
        person = init_person(message)
    text = ""
    for student in person.get_students():
        text += f"{student.name}\n"
    if not text:
        bot.send_message(person.user_id, text="У вас еще нет учеников")

    else:
        bot.send_message(person.user_id, text=text)

    navigation(message, person)



class Downloader_task:
    instance = None

    def __init__(self, message: Message, person: Tutor):
        self.student: Student | None = None
        self.photo_paths = []
        self.message = message
        self.person = person

    def download_task(self):
        self.__class__.instance = self
        self.choice_student()

    def choice_student(self):
        keyboard = tb.types.ReplyKeyboardMarkup(resize_keyboard=True)
        students = self.person.get_students()
        students_dict = dict()

        for student in students:
            button = KeyboardButton(text=student.name)
            keyboard.add(button)
            students_dict[student.name] = student.user_id

        back_nav = KeyboardButton(text="Назад")
        keyboard.add(back_nav)
        msg = bot.send_message(self.person.user_id, text="Выбери ученика:", reply_markup=keyboard)

        bot.register_next_step_handler(msg, self.define_student, students_dict)

    def define_student(self, message: Message, students_dict: dict):
        text = message.text
        if text == "Назад":
            navigation(message, self.person)
            return
        elif text not in students_dict.keys():
            bot.send_message(self.person.user_id,
                             text="Введено неверное имя ученика. Следующий раз попробуйте просто нажать на клавиатуру", reply_markup=ReplyKeyboardRemove())
            navigation(message, self.person)
            return

        keyboard = tb.types.ReplyKeyboardMarkup(resize_keyboard=True)
        button1 = KeyboardButton(text="Отправлю скрины условий")
        button2 = KeyboardButton(text="Отправлю pdf, docx или doc файлом")
        keyboard.add(button1)
        keyboard.add(button2)

        self.student = Student(int(students_dict[text]))
        msg = bot.send_message(self.person.user_id, text="Выбери способ добавления дз:", reply_markup=keyboard)
        bot.register_next_step_handler(msg, self.define_method_for_sending)

    def define_method_for_sending(self, message: Message):
        if message.text == "Отправлю скрины условий":
            bot.send_message(self.person.user_id, text="Отправьте одним сообщением все изображения с условиями. Один скрин - одно задание. Количество скринов должно совпадать с количеством ответов! После отправки всех условий нажмите /done", reply_markup=ReplyKeyboardRemove())
            permission_to_receive_photo.change_permission(value=True)

        elif message.text == "Отправлю pdf, docx или doc файлом":
            msg = bot.send_message(self.person.user_id, text="Присылайте файл.", reply_markup=ReplyKeyboardRemove())
            bot.register_next_step_handler(msg, self.define_file)

        else:
            bot.send_message(self.person.user_id, text="Ошибка. Следующий раз воспользуйтесь клавиатурой", reply_markup=ReplyKeyboardRemove())
            navigation(message, self.person)

    def define_photos(self, msg: Message):
        if msg.photo:
            file_id = msg.photo[-1].file_id
            self.photo_paths.append(bot.get_file(file_id).file_path)
        elif self.photo_paths:
            self.stop_receiving_photo(msg)
        else:
            bot.send_message(self.person.user_id, text="Ошибка. Вам необходимо отправить изображение.")
            navigation(self.message, self.person)

    def stop_receiving_photo(self, message: Message):
        if not permission_to_receive_photo.get_permission():
            return

        permission_to_receive_photo.change_permission(value=False)
        jpg_files = []
        if self.photo_paths:
            for path in self.photo_paths:
                jpg_files.append(Jpg_file(bot.download_file(path)))
        else:
            bot.send_message(self.person.user_id, text="Необходимо прикрипить изображения")

        homework = HomeworkDocument(*list(map(repr, jpg_files)))
        file = homework.get_file()
        file.name = self.student.name
        requests.add_new_dz(self.student.user_id, repr(file))
        msg = bot.send_message(self.person.user_id,
                               text='Супер! Домашняя работа загрузилась и уже доставлена ученику! Пора загрузить ответы. \n\n Ответы вводятся <b>одной</b> строкой, разделяются <b>одним</b> пробелом. Количество ответов должно совпадать с количеством заданий!',
                               parse_mode='HTML')

        self.sendler = Sender_dz(person=self.person, student=self.student, recipient=self.student,  dz_number=requests.select_last_dz_id(self.student.user_id))
        self.sendler.start()
        bot.register_next_step_handler(msg, self.define_answers)

    def define_file(self, message: Message):
        try:
            file_info = bot.get_file(message.document.file_id)
            file = File_faсtory(bot.download_file(file_info.file_path), file_info.file_path.split('.')[-1])
            file.name = self.student.name
            file.convert_to_pdf()
        except AttributeError:
            bot.send_message(self.person.user_id, text="Ошибка чтения файла. Необходимо прикрепить файл.")
            navigation(message, self.person)
            return

        requests.add_new_dz(self.student.user_id, str(file))
        msg = bot.send_message(self.person.user_id,
                               text='Супер! Домашняя работа загрузилась и уже доставлена ученику! Пора загрузить ответы. \n\n Ответы вводятся <b>одной</b> строкой, разделяются <b>одним</b> пробелом. Количество ответов должно совпадать с количеством заданий!',
                               parse_mode='HTML')

        self.sendler = Sender_dz(person=self.person, student=self.student,recipient=self.student, dz_number=requests.select_last_dz_id(self.student.user_id))
        self.sendler.start()
        bot.register_next_step_handler(msg, self.define_answers)

    def define_answers(self, message: Message):
        answers = list(map(lambda x: x.lower(), message.text.split()))
        dz_id = requests.select_last_dz_id(self.student.user_id)
        self.number_task = 0

        for answer in answers:
            self.number_task += 1
            requests.add_answer_for_dz(dz_id, self.student.user_id, self.number_task, answer)

        keyboard = InlineKeyboardMarkup()

        callback_data_comment = Callback_data("add_comment")
        callback_data_comment.add_items(
            ('person_id', self.person.user_id),
            ('student_id', self.student.user_id),
            ('message_id', self.sendler.comment.message_id)
        )
        bot.add_callback(callback_data_comment)
        button1 = InlineKeyboardButton(text="Добавить комментарий", callback_data=str(bot.callback_list.index(callback_data_comment)))

        callback_data_add_file = Callback_data('add_additional_files')
        callback_data_add_file.add_items(
            ('person_sendler_id', self.person.user_id),
            ('student_id', self.student.user_id),
            ('student_name', self.student.name),
            ('dz_number', self.sendler.dz_number),
        )
        bot.add_callback(callback_data_add_file)
        button2 = InlineKeyboardButton(text="Добавить доп. файлы", callback_data=str(bot.callback_list.index(callback_data_add_file)))

        keyboard.add(button1, button2)
        msg = bot.send_message(self.person.user_id, text=f"<b><i>МЕНЮ ДЗ</i></b>\nУченик: {self.student.name}\nНомер дз: {self.sendler.dz_number}\nКоличество заданий: {self.number_task}\n\n<i>При обнаружении ошибки: /mistake</i>", parse_mode="HTML", reply_markup=keyboard)



@bot.message_handler(func=permission_to_receive_photo.get_permission, content_types=['photo'])
def download_photos_for_dz(message: Message):
    dt = Downloader_task.instance
    dt.define_photos(message)


@bot.message_handler(func=permission_to_receive_photo.get_permission, commands=[cmd.get_stop_sending_photo()])
def stop_download_photos_for_dz(message: Message):
    dt = Downloader_task.instance
    dt.stop_receiving_photo(message)

@bot.message_handler(commands=[cmd.get_last_dz()])
def get_last_dz(message: Message, person: Student | None = None):
    if person is None:
        person = init_person(message)
    number = requests.select_last_dz_id(person.user_id)
    if number:
        Sender_dz(person=person, recipient=person,  dz_number=number).start()
    else:
        bot.send_message(person.user_id, text="У вас еще нет домашек")
        navigation(message, person)


class Sender(ABC):
    def __init__(self, person, recipient: Tutor | Student, student: Student=None, dz_number:int =None):
        self.person = person
        self.recipient = recipient
        if dz_number is not None:
            self.dz_number = dz_number

        if student is not None:
            self.student = student
        elif isinstance(person, Student):
            self.student = person

    def start(self):
        if isinstance(self.person, Tutor) and not hasattr(self, 'student'):
            self.define_student()
        elif isinstance(self.person, Tutor) and not hasattr(self, 'dz_number'):
            self.define_number()
        elif isinstance(self.person, Tutor):
            self.send()

        if isinstance(self.person, Student) and not hasattr(self, 'dz_number'):
            self.define_number()
        elif isinstance(self.person, Student) :
            self.send()

    def define_student(self):

        self.students_dict = dict()
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        students = self.person.get_students()

        for student in students:
            button = KeyboardButton(text=student.name)
            self.students_dict[student.name] = student.user_id
            keyboard.add(button)
        back = KeyboardButton(text="Назад")
        keyboard.add(back)
        msg = bot.send_message(self.person.user_id, text="Выбор ученика", reply_markup=keyboard)

        bot.register_next_step_handler(msg, self.get_student)

    def get_student(self, message):
        if message.text == "Назад":
            navigation(message, self.person)
            return
        elif message.text not in self.students_dict.keys():
            bot.send_message(self.person.user_id,
                             text="Введено неверное имя ученика. Попробуйте просто нажать на клавиатуру", reply_markup=ReplyKeyboardRemove())
            return
        self.student = Student(int(self.students_dict[message.text]))

        if not hasattr(self, 'dz_number'):
            self.define_number()
        else:
            self.send()
    def define_number(self):

        self.counter_dz_for_student = requests.count_dz_for_student(self.student.user_id)
        msg = bot.send_message(self.person.user_id, text=f"Введите номер дз, которое хотите получить."
                                                    f"Всего домашних работ: {self.counter_dz_for_student}", reply_markup=ReplyKeyboardRemove())

        bot.register_next_step_handler(msg, self.get_number)

    def get_number(self, message: Message):
        text = message.text
        try:
            self.dz_number = int(text)
        except Exception:
            bot.send_message(self.person.user_id, text="Неверено введен номер дз.")
            navigation(message, self.person)
            return

        if 0 < self.dz_number <= self.counter_dz_for_student:
            self.send()
        else:
            bot.send_message(self.person.user_id, text="Домашней работы с таким номером не существует")
            navigation(message, self.person)

    @abstractmethod
    def send(self):
        pass

class Sender_answer(Sender):

    def send(self):
        answers = "\n".join(list(map(lambda x: ': '.join((str(x[0]), x[1])), requests.select_answers(self.dz_number, self.student.user_id)._items())))

        msg = bot.send_message(self.person.user_id, text=f"Ответы для {self.student.name} по домашке dz-{self.dz_number}:\n{answers}", reply_markup=ReplyKeyboardRemove())
        navigation(msg, self.person)


class Sender_dz(Sender):
    def send(self):
        self.file_name = f"dz-{self.dz_number}.pdf"
        path = requests.select_path_to_file(self.dz_number, self.student.name)
        self.comment = bot.send_message(self.recipient.user_id, text="Домашнее задание:", is_deleting=isinstance(self.recipient, Tutor))
        try:
            file = open(path, "rb")
            bot.send_document(self.recipient.user_id, document=file, visible_file_name=self.file_name, is_deleting=isinstance(self.recipient, Tutor))
        except FileNotFoundError as ex:
            print(ex)
            bot.send_message(self.person.user_id, text="Ошибка", reply_markup=ReplyKeyboardRemove())


class Checker_dz:

    def __init__(self, person: Student):
        self.person = person
    def check_dz(self):
        self.define_dz()

    def define_dz(self):
        counter = requests.count_dz_for_student(self.person.user_id)
        msg = bot.send_message(self.person.user_id,
                               text=f"Введите номер домашней работы, на которую вы хотите дать ответ. Последняя домашняя работа: dz-{counter}")

        bot.register_next_step_handler(msg, self.define_answer)
    def define_answer(self, message: Message):
        text = message.text
        try:
            self.dz_id = int(text)
        except ValueError:
            bot.send_message(self.person.user_id,
                             text="Введено неверное значение. Необходимо вводить только одно число - номер дз")
            navigation(message, self.person)
            return

        if not 0 < self.dz_id <= requests.count_dz_for_student(self.person.user_id):
            bot.send_message(self.person.user_id, text="Домашней работы с таким номером не существует")
            navigation(message, self.person)
            return

        if requests.select_has_answer_in_dz(self.dz_id, self.person.user_id):
            bot.send_message(self.person.user_id, text="Ответ для домашней работы уже был дан. Результаты изменить нельзя")
            navigation(message, self.person)
            return

        msg = bot.send_message(self.person.user_id,
                               text=f"Вводите ответы для dz-{self.dz_id}\n. Инструкция по оформлению ответа: /get_manual")
        bot.register_next_step_handler(msg, self.check_answers)

    def check_answers(self, message: Message):
        answers = list(map(lambda x: x.lower(), message.text.split()))
        correct_answers = requests.select_answers(self.dz_id, self.person.user_id)
        if len(answers) != len(correct_answers):
            bot.send_message(self.person.user_id, text="Введено неверное количество ответов")
            navigation(message, self.person)
            return

        number_correct_answer = sum(
            list(correct_answers.values())[i] == answers[i] for i in range(len(correct_answers)))
        requests.update_answer_in_answers(self.dz_id, self.person.user_id, answers)
        requests.change_has_answer_in_dz(self.dz_id, self.person.user_id)
        bot.send_message(self.person.user_id,
                         text=f"Для домашней работы dz-{self.dz_id} введено {number_correct_answer} из {len(answers)} верных ответов. Результаты отправлены преподавателю.",
                         is_deleting=False)
        tutor = self.person.get_tutor()

        result = ""
        for i in range(len(answers)):
            result += f"{i + 1}) {correct_answers[i + 1]} / {answers[i]}\n"
        bot.send_message(tutor.user_id,
                         text=f"{self.person.name} выполнил домашнюю работу: dz-{self.dz_id}. Результат: {number_correct_answer} из {len(answers)}.\n{result}",
                         is_deleting=False)
        navigation(message,self.person)

@bot.message_handler(commands=[cmd.get_dz_by_number()])
def get_dz_by_number(person: Student):
    Sender_dz(person=person, recipient=person).start()

@bot.message_handler(commands=[cmd.get_manual()])
def get_manual(message: Message):
    bot.send_message(message.chat.id, text="Ответы в одну строку через пробел. Количество ответов обязательно должно совпадать с количеством заданий в условии!"
                                           "Если в одном из заданий ответ состоит из двух или более слов, "
                                           "то вместо пробелов в этом ответе используйте: <b>_</b>\nЕсли на задание нельзя дать ответ в письменном виде, "
                                           "например если это математический график или программа на языке программимрования, то ставьте вместо ответа: <b>—</b>.\n"
                                           "Например ответ на дз может выглядеть следующим образом:\n<b>236 12.4 город_Москва — — —</b>\nВ данном примере было предоставлено 6 ответов.", parse_mode="HTML")
    navigation(message)

@bot.callback_query_handler(func=lambda callback: int(callback.data) < len(bot.callback_list) and bot.callback_list[int(callback.data)].name == 'add_additional_files')
def define_additional_files(callback):
    callback_data = bot.get_callback(int(callback.data))
    msg = bot.send_message(callback_data.get_value('person_sendler_id'), text="Отправьте доп файлы одним zip-архивом")
    bot.register_next_step_handler(msg, add_addtional_files, callback_data)

def add_addtional_files(message: Message, callback_data):
    try:
        file_info = bot.get_file(message.document.file_id)
        file = File_faсtory(bot.download_file(file_info.file_path), file_info.file_path.split('.')[-1])
    except Exception as ex:
        print(ex)
        msg = bot.send_message(callback_data.get_value('person_sendler_id'), text="Ошибка при добавлении файла")
        return
    file.name = requests.select_path_to_file(callback_data.get_value('dz_number'), callback_data.get_value('student_name')).split("/")[-1][:-4]
    requests.add_additional_files(callback_data.get_value('dz_number'), callback_data.get_value('student_id'), repr(file))

    bot.send_document(chat_id=callback_data.get_value('student_id'), document=open(repr(file), 'rb'), visible_file_name=f'Дополнительные файлы для dz-{callback_data.get_value("dz_number")}.zip', is_deleting=False)


@bot.callback_query_handler(func=lambda callback: int(callback.data) < len(bot.callback_list) and bot.callback_list[int(callback.data)].name == 'add_comment')
def define_comment(callback):
    callback_data = bot.get_callback(int(callback.data))
    msg = bot.send_message(chat_id=callback_data.get_value('person_id'), text="Вводите комментарий")
    bot.register_next_step_handler(msg, add_comment, callback_data)

def add_comment(message: Message, callback_data):
    comment = message.text
    if comment:
        msg = bot.edit_message_text(chat_id=callback_data.get_value('student_id'), message_id=callback_data.get_value('message_id'), text=f"Домашняя работа\n{comment}")
        bot.send_message(chat_id=callback_data.get_value('person_id'), text="Комментарий успешно добавлен")


@bot.message_handler(func=lambda x: True)
def prompt_in_case_of_incorrect_input(message):
    bot.send_message(message.chat.id, text="Некорректный ввод. Нажмите на: /start")

if __name__ == '__main__':
    try:
        bot.infinity_polling()
    except Exception as ex:
        print(ex)
        time.sleep(15)

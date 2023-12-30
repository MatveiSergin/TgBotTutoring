import telebot as tb
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from telebot.types import Message
from config import config
from roles import Student, Tutor
from actions import Action
from database.requests import select_person, select_all_persons

bot = tb.TeleBot(token=config.TOKEN)

@bot.message_handler(commands=["start"])
def welcome(message: Message):
    user_id = message.chat.id
    bot.send_message(user_id, text="Привет!")

    if select_person(user_id, "tutor"):
        person = Tutor(user_id)
    else:
        person = Student(user_id)

    if person.isvalid():

        navigation_for_student(message, person)

    if isinstance(person, Tutor):
        bot.send_message(user_id, text="Вы не репетитор!")
    elif isinstance(person, Student):
        registration(message, person)
    else:
        bot.send_message(user_id, text="Какая - то ошибка")
        raise TypeError("Person is Null")

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
            tutor = data[1]
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
@bot.message_handler(commands=["nav"])
def navigation_for_student(message: Message, person: Student | None = None):
    if person is None:
        welcome(message)

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

@bot.message_handler(commands=["action"])
def navigation_for_student(message: Message, person: Tutor | None | Student = None):
    if person is None:
        welcome(message)
    if isinstance(person, Student):
        bot.send_message(person.user_id, text="Ошибка допуска")
        navigation_for_student(message, person)

    keyboard = tb.types.ReplyKeyboardMarkup(resize_keyboard=True)
    button1 = KeyboardButton(text="Загрузка дз")

def define_person_action(message: Message, person: Student):
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
            action.download_task() if isinstance(person, Tutor) else None

def choice_student(message: Message, person: Tutor):
    pass


if __name__ == '__main__':
    bot.polling()
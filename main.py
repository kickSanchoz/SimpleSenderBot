# Import smtplib for the actual sending function
import smtplib
# Import the email modules we'll need
from email.message import EmailMessage

import telebot
import re
import threading
import time

BOT_TOKEN = "censored"
url = "https://api.telegram.org/bot{}/".format(BOT_TOKEN)
regex = r"\/send\s*(?:(-m\s+[\wА-Яа-я\.\!\?\s\,]+)|(-t\s+[\wА-Яа-я\.\!\?\s\,]+)|(-d\s+(?:[\w.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9]+(?:,|\s)*)+)|(-w\s+[\wА-Яа-я\.\!\?\s\,]+))+"

bot = telebot.TeleBot(BOT_TOKEN)

time_delay = {"сейчас": 0,
              "через 15 сек": 15,
              "через 30 сек": 30}


class Shipment(threading.Thread):
    def __init__(self, letter, time_sleep):
        super().__init__()
        self.letter = letter
        self.time_sleep = time_sleep

    def run(self):
        time.sleep(self.time_sleep)
        print(threading.currentThread().getName())
        # print(self.offset)

        # Send the message via our own SMTP server.
        sender = smtplib.SMTP('smtp.gmail.com', 587)
        sender.starttls()
        sender.login("censored", "censored")
        sender.send_message(self.letter)
        sender.quit()
        print(threading.currentThread().getName() + " is done")


def prepare_shipment(message, msg_content, theme, destination, when):
    """
    Prepare message before shipment
    """

    # if -w not defined then take first value from available
    if when is not None:
        time_sleep = time_delay[when.rstrip()]
    else:
        time_sleep = time_delay[next(iter(time_delay))]
        when = next(iter(time_delay))

    msg = EmailMessage()
    # Message content
    msg.set_content(msg_content)

    # Theme of letter
    if theme is None:
        msg['Subject'] = "Тестовое письмо"
    else:
        msg['Subject'] = theme
    msg['From'] = "censored"
    msg['To'] = [destination]

    bot.send_message(message.chat.id, "Сообщение будет оправлено {}".format(when))

    thread = Shipment(letter=msg, time_sleep=time_sleep)
    thread.start()


# Обязательные параметры: -m -d. Необязательные -t -w
def make_error(msg_content, theme, destination, when="сейчас"):
    final_error = ""

    if msg_content is None:
        final_error += "Необходимо указать сообщение письма (<i>-w Ваше сообщение</i>)\n"
    if destination is None:
        final_error += "Необходимо указать адрес(а) получателя (<i>-d first_email@example.com, " \
                       "second_email@example.com</i>)\n "
    if when is not None and when.rstrip() not in time_delay:
        final_error += "Неправильно указано время доставки, для справки \"/help\""

    return final_error


@bot.message_handler(commands=['start', 'help'])
def start_command(message):
    allow_timing = ""
    for timing in time_delay:
        allow_timing += timing
        if timing != list(time_delay.keys())[-1]:
            allow_timing += "/"

    help_message = "Для работы с ботом, необходимо ввести сообщение в строчку по следующим правилам:\n" \
                   "/send \n" \
                   "<b>-m ваше сообщение</b>\n" \
                   "<i>-t тема письма</i> (по умолч. \"Тестовое письмо\")\n" \
                   "<b>-d список электронных адресов через запятую (пример: email@example.com)</b>\n" \
                   "<i>-w время отправки</i> (по умолч. сейчас). Доступные варианты: {}".format(allow_timing)
    bot.send_message(message.chat.id, help_message, parse_mode='html')
    print(message.text)


@bot.message_handler(commands=['send'])
def send_command(message):
    received_message = message.text

    result = re.match(regex, received_message)

    msg_content, theme, destination, when = None, None, None, None

    for group in result.groups():
        if group is not None:
            if group.startswith("-m"):
                msg_content = group.split("-m ")[1]
            elif group.startswith("-t"):
                theme = group.split("-t ")[1]
            elif group.startswith("-d"):
                destination = group.split("-d ")[1]
            elif group.startswith("-w"):
                when = group.split("-w ")[1]

    error = make_error(msg_content, theme, destination, when)
    if error == "":
        prepare_shipment(message, msg_content, theme, destination, when)
    else:
        bot.send_message(message.chat.id, error, parse_mode='html')


@bot.message_handler(content_types=['text'])
def default_message(message):
    advice = "Для работы с ботом, необходимо ввести сообщение в строчку по следующим правилам:\n" \
             "/send \n" \
             "<b>-m ваше сообщение</b>\n" \
             "<i>-t тема письма</i> (по умолч. \"Тестовое письмо\")\n" \
             "<b>-d список электронных адресов через запятую (пример: email@example.com)</b>\n" \
             "<i>-w время отправки</i> (по умолч. сейчас)"
    bot.send_message(message.chat.id, advice, parse_mode='html')

    # thread = Shipment(message.text)
    # thread.start()


bot.polling(none_stop=True)

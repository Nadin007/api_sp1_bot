import logging
import os
import time

import requests
from dotenv import load_dotenv
from telegram import Bot

logger = logging.getLogger('My_logger')
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter(
    '%(asctime)s, %(levelname)s, %(message)s, %(name)s')
handler = logging.FileHandler('bug_report.log')
handler.setFormatter(formatter)

logger.addHandler(handler)

load_dotenv()

PRAKTIKUM_TOKEN = os.getenv('PRAKTIKUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# проинициализируйте бота здесь,
# чтобы он был доступен в каждом нижеобъявленном методе,
# и не нужно было прокидывать его в каждый вызов
bot = Bot(token=TELEGRAM_TOKEN)
headers = {'Authorization': 'OAuth ' + PRAKTIKUM_TOKEN}
url = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'


def parse_homework_status(homework):
    homework_name = homework['homework_name']
    if homework['status'] != 'approved':
        verdict = 'К сожалению, в работе нашлись ошибки.'
    else:
        verdict = 'Ревьюеру всё понравилось, работа зачтена!'
    return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def get_homeworks(current_timestamp):
    homework_statuses = requests.get(url, headers=headers, params={
        'from_date': current_timestamp})
    return homework_statuses.json()


def send_message(message):
    return bot.send_message(chat_id=CHAT_ID, text=message)


def main():
    logger.debug('Bot started.')
    current_timestamp = int(time.time())  # Начальное значение timestamp
    while True:
        try:
            homework = get_homeworks(current_timestamp)['homeworks']
            if len(homework) > 0:
                message = parse_homework_status(homework[0])
                send_message(message)
                logger.info('Messege was sent.')
                current_timestamp = int(time.time())
            time.sleep(5 * 60)  # Опрашивать раз в пять минут

        except Exception as e:
            message = f'Бот упал с ошибкой: {e}'
            logger.error(message)
            send_message(message)
            time.sleep(5)


if __name__ == '__main__':
    main()

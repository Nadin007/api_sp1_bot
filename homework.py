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

HEADERS = {'Authorization': 'OAuth ' + PRAKTIKUM_TOKEN}
URL = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'
STATUSES = {
    'rejected': 'У вас проверили работу "{0}"!\n\n'
                'К сожалению, в работе нашлись ошибки.',
    'approved': 'У вас проверили работу "{0}"!\n\n'
                'Ревьюеру всё понравилось, работа зачтена!',
    'reviewing': 'Ваша работа "{0}" на стадии проверки ревьювером!'}
SLEEP_TIME = 300

bot = Bot(token=TELEGRAM_TOKEN)


def parse_homework_status(homework):
    if 'homework_name' in homework and 'status' in homework:
        homework_name = homework['homework_name']
        status = homework['status']
        if status in STATUSES:
            return STATUSES[status].format(homework_name)
        else:
            logger.info('New homework status was found.')
            return f'А это что-то новенькое - {status}!'
    else:
        raise Exception(
            "Response should contain homework_name and status keys")


def get_homeworks(current_timestamp):
    try:
        homework_statuses = requests.get(URL, headers=HEADERS, params={
            'from_date': current_timestamp})
    except requests.exceptions.HTTPError as err:
        raise Exception(
            "request failed with a HTTPError with current_timestamp = "
            f"{current_timestamp} URL = {URL}") from err
    except requests.exceptions.ConnectionError as err:
        raise Exception(
            "request failed with a ConnectionError with current_timestamp = "
            f"{current_timestamp} URL = {URL}"
        ) from err
    except requests.exceptions.ConnectTimeout as err:
        raise Exception(
            "request failed with a ConnectTimeout with current_timestamp = "
            f"{current_timestamp} URL = {URL}"
        ) from err
    except requests.exceptions.RequestException as err:
        raise Exception(
            "request failed with a RequestException with current_timestamp = "
            f"{current_timestamp} URL = {URL}"
        ) from err
    except requests.exceptions.TooManyRedirects as err:
        raise Exception(
            "request failed with a TooManyRedirects with current_timestamp = "
            f"{current_timestamp} URL = {URL}"
        ) from err
    try:
        return homework_statuses.json()
    except ValueError as err:
        raise Exception(
            "Server sent invalid json current_timestamp = "
            f"{current_timestamp} URL = {URL}"
        ) from err


def send_message(message):
    return bot.send_message(chat_id=CHAT_ID, text=message)


def main():
    logger.debug('Bot started.')
    current_timestamp = int(time.time())
    while True:
        try:
            homework = get_homeworks(current_timestamp)['homeworks']
            if len(homework) > 0:
                message = parse_homework_status(homework[0])
                send_message(message)
                logger.info('Messege was sent.')
                current_timestamp = int(time.time())
            time.sleep(SLEEP_TIME)

        except Exception as e:
            message = f'Бот упал с ошибкой: {e}, {e.__cause__}'
            logger.error(message)
            send_message(message)
            time.sleep(SLEEP_TIME)


if __name__ == '__main__':
    main()

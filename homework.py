import logging
import os
import time
from json.decoder import JSONDecodeError

import requests
from dotenv import load_dotenv
from telegram import Bot

logger = logging.getLogger(__name__)
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
URL = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
STATUSES = {
    'rejected': 'У вас проверили работу "{0}"!\n\n'
                'К сожалению, в работе нашлись ошибки.',
    'approved': 'У вас проверили работу "{0}"!\n\n'
                'Ревьюеру всё понравилось, работа зачтена!',
    'reviewing': 'Ваша работа "{0}" на стадии проверки ревьювером!'}
SLEEP_TIME = 900

bot = Bot(token=TELEGRAM_TOKEN)


def send_message(message):
    return bot.send_message(chat_id=CHAT_ID, text=message)


def log_error(e):
    message = f'Бот упал с ошибкой: {e}, {e.__cause__}'
    logger.error(message)
    send_message(message)


def log_func_error(func):
    def wrapper(*args):
        try:
            return func(*args)
        except Exception as e:
            log_error(e)
            raise e
    return wrapper


class InvalidHWServerResponse(ValueError):
    pass


@log_func_error
def parse_homework_status(homework):
    if 'homework_name' not in homework or 'status' not in homework:
        raise InvalidHWServerResponse(
            "Response should contain homework_name and status keys")

    homework_name = homework['homework_name']
    status = homework['status']
    if status in STATUSES:
        return STATUSES[status].format(homework_name)
    else:
        logger.warn('New homework status was found.')
        return f'А это что-то новенькое - {status}!'


@log_func_error
def get_homeworks(current_date):
    try:
        homework_statuses = requests.get(URL, headers=HEADERS, params={
            'from_date': current_date})
    except requests.exceptions.RequestException as err:
        raise Exception(f"Request failed with a {err} and params: "
                        f"current_timestamp = {current_date} URL = {URL}"
                        ) from err

    try:
        return homework_statuses.json()
    except JSONDecodeError as err:
        raise Exception(
            "Server sent invalid json current_timestamp = "
            f"{current_date} URL = {URL}"
        ) from err


@log_func_error
def parse_homeworks(response):
    if response is None or 'homeworks' not in response:
        raise InvalidHWServerResponse(
            "Response should contain 'homeworks' as a key")

    return response['homeworks']


def main():
    logger.debug('Bot started.')
    current_timestamp = int(time.time())
    while True:
        try:
            response = get_homeworks(current_timestamp)
            homeworks = parse_homeworks(response)
            if len(homeworks) > 0:
                message = parse_homework_status(homeworks[0])
                send_message(message)
                logger.info('Messege was sent.')
                current_timestamp = int(time.time())
            time.sleep(SLEEP_TIME)

        except Exception:
            time.sleep(SLEEP_TIME)


if __name__ == '__main__':
    main()

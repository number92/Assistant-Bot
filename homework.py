import logging
import sys
import requests
import os
import telegram
import time
from http import HTTPStatus
from dotenv import load_dotenv
from exceptions import UnxpectedHTTPStatusError

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

EPOCH_TIMESTAMP = time.gmtime(1680516000)  # 03.04.2023 Начало 7 спринта
RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens() -> bool:
    """Проверка наличия токенов в окружениии переменных."""
    tokens = [PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]
    if all(tokens):
        return tokens
    else:
        return False


def send_message(bot, message) -> None:
    """Отправка сообщения в телеграмм."""
    try:
        logging.info('Отправка сообщения в мессенджер...')
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.debug('Сообщение отправлено в мессенджер')
    except telegram.error.TelegramError as err:
        logging.error(f'Ошибка при отправке сообщения:{err}')
        raise ConnectionError(f'Ошибка при отправке сообщения:{err}')


def get_api_answer(timestamp: int) -> dict:
    """Запрос API сервиса."""
    params = {'from_date': (timestamp)}
    try:
        logging.debug('Запрос API сервиса...')
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except OSError as err:
        logging.error(f'Ошибка в запросе API{err}')
        raise ConnectionError(
            'Не удалось установить соединение с сервером') from err
    if response.status_code != HTTPStatus.OK:
        logging.error(f'Статус запроса {response.status_code}')
        raise UnxpectedHTTPStatusError(
            f'Статус запроса {response.status_code}')
    else:
        logging.debug('Ответ от Api получен')
        return response.json()


def check_response(response: dict) -> list:
    """Проверка Ответа API."""
    logging.debug('Проверка Ответа API')
    if not isinstance(response, dict):
        raise TypeError('Ожидаемый тип данных словарь,'
                        f'Тип данных {type(response)}')
    homework = response.get('homeworks')
    current_date = response.get('current_date')
    if not isinstance(homework, list):
        raise TypeError('Ожидаемый тип данных список,'
                        f'Тип данных {type(homework)}')
    if not isinstance(current_date, int):
        raise TypeError('Ожидаемый тип данных целое число,'
                        f'Тип данных {type(current_date)}')
    if not response.keys():
        raise KeyError('Один из ожидаемых ключей отсутствует')
    logging.debug('Проверка ответа пройдена')
    return homework


def parse_status(homework: dict) -> str:
    """Извлечение статуса ДЗ."""
    homework_name = homework.get('homework_name')
    status = homework.get('status')
    if not homework_name:
        raise KeyError('"homework_name" не найдено')
    if status not in HOMEWORK_VERDICTS.keys():
        raise KeyError(f'{status} не соответсвует ни одному из ожидаемых')
    if len(homework) == 0:
        logging.info('Значение "homework" пустое, статус не обновлен')
    verdict = HOMEWORK_VERDICTS[status]
    return (f'Изменился статус проверки работы "{homework_name}". {verdict}')


def main():
    """Основная логика работы бота."""
    if check_tokens() is False:
        err_message = 'Один из ключей переменных отсутствует'
        logging.critical(err_message)
        sys.exit(err_message)
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    last_message = ''
    last_err = ''
    while True:
        try:
            response = get_api_answer(timestamp)
            if not response.keys():
                logging.error('отсутствуют ожидаемые ключи в ответе API')
            homeworks = check_response(response)
            if homeworks:
                homeworks = homeworks[0]
                message = parse_status(homeworks)
                if last_message != message:
                    send_message(bot, message)
                    last_message = message
            else:
                logging.debug('Статус работы не обновлен.')
                timestamp = response.get('current_date')
                last_err = ''
        except Exception as error:
            message_err = f'Сбой в работе программы: {error}'
            logging.error(message_err, exc_info=True)
            if last_err != message_err:
                send_message(bot, message_err)
                last_err = message_err
        finally:
            logging.debug('Следующий запрос проверки через 10 мин.')
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        stream=sys.stdout,
        encoding='utf-8',
        format='%(asctime)s, %(levelname)s, %(message)s',
    )
    main()

import logging

from requests import RequestException

from exceptions import ParserFindTagException


def get_response(session, url):
    try:
        response = session.get(url)
        response.encoding = 'utf-8'
        return response
    except RequestException:
        logging.exception(
            f'Возникла ошибка при загрузке страницы {url}',
            stack_info=True
        )


def find_tag(soup, tag, attrs=None):
    searched_tag = soup.find(tag, attrs=(attrs or {}))
    if searched_tag is None:
        error_msg = f'Не найден тег {tag} {attrs}'
        logging.error(error_msg, stack_info=True)
        raise ParserFindTagException(error_msg)
    return searched_tag


def find_siblings(soup, search='next'):
    searched_tag = (soup.find_next_sibling() if search == 'next'
                    else soup.find_previous_sibling())
    if searched_tag is None:
        error_message = 'Сиблинг тэг не найден'
        logging.error(error_message, stack_info=True)
        raise ParserFindTagException(error_message)
    return searched_tag

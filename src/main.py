import logging
import re
import requests_cache

from bs4 import BeautifulSoup
from tqdm import tqdm
from urllib.parse import urljoin

from configs import configure_argument_parser, configure_logging
from constants import BASE_DIR, EXPECTED_STATUS, MAIN_DOC_URL, PEP_INDEX_URL
from exceptions import ParserFindUrlException
from outputs import control_output
from utils import find_siblings, find_tag, get_response


def whats_new(session):
    whats_new_url = urljoin(MAIN_DOC_URL, 'whatsnew/')
    response = get_response(session, whats_new_url)
    if response is None:
        return

    soup = BeautifulSoup(response.text, features='lxml')
    main_div = find_tag(soup, 'section', attrs={'id': 'what-s-new-in-python'})
    div_with_ul = find_tag(main_div, 'div', attrs={'class': 'toctree-wrapper'})
    sections_by_python = div_with_ul.find_all(
        'li',
        attrs={'class': 'toctree-l1'}
    )
    results = [('Ссылка на статью', 'Заголовок', 'Редактор, Автор')]
    for section in tqdm(sections_by_python):
        version_a_tag = find_tag(section, 'a')
        href = version_a_tag['href']
        version_link = urljoin(whats_new_url, href)
        response = get_response(session, version_link)
        if response is None:
            continue
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, features='lxml')
        h1 = find_tag(soup, 'h1')
        dl = find_tag(soup, 'dl')
        dl_text = dl.text.replace('\n', ' ')
        results.append(
            (version_link, h1.text, dl_text)
        )
    return results


def latest_versions(session):
    response = get_response(session, MAIN_DOC_URL)
    if response is None:
        return

    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'lxml')
    sidebar = find_tag(soup, 'div', {'class': 'sphinxsidebarwrapper'})
    ul_tags = sidebar.find_all('ul')
    for ul in ul_tags:
        if 'All versions' in ul.text:
            a_tags = ul.find_all('a')
            break
    else:
        raise ParserFindUrlException('Не найден список c версиями Python')

    results = [('Ссылка на документацию', 'Версия', 'Статус')]
    pattern = r'Python (?P<version>\d\.\d+) \((?P<status>.*)\)'
    for a_tag in a_tags:
        link = a_tag['href']
        text_match = re.search(pattern, a_tag.text)
        if text_match is not None:
            version, status = text_match.groups()
        else:
            version, status = a_tag.text, ''
        results.append(
            (link, version, status)
        )
    return results


def download(session):
    downloads_url = urljoin(MAIN_DOC_URL, 'download.html')
    downloads_dir = BASE_DIR / 'downloads'
    downloads_dir.mkdir(exist_ok=True)
    response = get_response(session, downloads_url)
    if response is None:
        return
    soup = BeautifulSoup(response.text, features='lxml')
    table = find_tag(soup, 'table', attrs={'class': 'docutils'})
    pdf_a4_tag = find_tag(table, 'a', {'href': re.compile(r'.+pdf-a4\.zip$')})
    pdf_a4_link = pdf_a4_tag['href']
    archive_url = urljoin(downloads_url, pdf_a4_link)
    filename = archive_url.split('/')[-1]
    archive_path = downloads_dir / filename
    response = get_response(session, archive_url)
    if response is None:
        return
    with open(archive_path, 'wb') as file:
        file.write(response.content)
    logging.info(f'Архив был загружен и сохранён: {archive_path}')


def pep(session):
    response = get_response(session, PEP_INDEX_URL)
    if response is None:
        return
    soup = BeautifulSoup(response.text, features='lxml')
    index_section = find_tag(soup, 'section', attrs={'id': 'numerical-index'})
    tbody_tag = find_tag(index_section, 'tbody')
    key_status_urls = []
    non_matching_statuses = []
    pep_refs = tbody_tag.find_all('td', string=re.compile(r'^\d+$'))
    for pep_ref in tqdm(pep_refs):
        key = find_siblings(pep_ref, 'prev').text[1:]
        pep_url = urljoin(PEP_INDEX_URL, pep_ref.a['href'])
        response = get_response(session, pep_url)
        if response is None:
            continue
        soup = BeautifulSoup(response.text, features='lxml')
        dl_tag = find_tag(soup, 'dl', {'class': 'rfc2822 field-list simple'})
        dt_tags = dl_tag.find_all('dt')
        for dt_tag in dt_tags:
            if 'Status' in dt_tag.text:
                status = find_siblings(dt_tag).text
                key_status_urls.append(status)
                if key not in EXPECTED_STATUS.keys():
                    non_matching_statuses.append(
                        f'Неизвестный ключ: {key}\n'
                        f'{pep_url}'
                    )
                    continue
                if status not in EXPECTED_STATUS[key]:
                    non_matching_statuses.append(
                        'Не совпадают статусы:\n'
                        f'{pep_url}\n'
                        f'Статус в карточке: {status}\n'
                        f'Ожидаемые статусы: {EXPECTED_STATUS[key]}'
                    )
                break

    status_counts = ({status: key_status_urls.count(status)
                      for status in key_status_urls})
    peps_per_status = list(status_counts.items())
    peps_per_status.sort(key=lambda status: status[0])
    total = sum(status_counts.values())
    header, footer = [('Status', 'Amount')], [('Total', total)]
    results = header + peps_per_status + footer

    if non_matching_statuses:
        for non_matching_status in non_matching_statuses:
            tqdm.write(non_matching_status)

    return results


MODE_TO_FUNCTION = {
    'whats-new': whats_new,
    'latest-versions': latest_versions,
    'download': download,
    'pep': pep,
}


def main():
    configure_logging()
    logging.info('Парсер запущен!')

    arg_parser = configure_argument_parser(MODE_TO_FUNCTION.keys())
    args = arg_parser.parse_args()
    logging.info(f'Аргументы командной строки: {args}')

    session = requests_cache.CachedSession()
    if args.clear_cache:
        session.cache.clear()

    parser_mode = args.mode
    results = MODE_TO_FUNCTION[parser_mode](session)

    if results is not None:
        control_output(results, args)
    logging.info('Парсер завершил работу.')


if __name__ == '__main__':
    main()

import logging
import os
import requests

from dotenv import load_dotenv
from itertools import count
from requests.exceptions import HTTPError
from statistics import mean
from terminaltables import AsciiTable


def get_salary_range_hh(vacancy):
    minimal_salary = vacancy['salary']['from']
    maximal_salary = vacancy['salary']['to']
    if vacancy['salary']['currency'] != 'RUR':
        minimal_salary, maximal_salary = None, None
    return minimal_salary, maximal_salary


def predict_salary(salary_from, salary_to):
    salary_to_coefficient = 0.8
    salary_from_coefficient = 1.2

    if not salary_from and not salary_to:
        return None
    elif salary_from and salary_to:
        mean_salary = (salary_from + salary_to) / 2
    elif salary_from:
        mean_salary = salary_from * salary_from_coefficient
    elif salary_to:
        mean_salary = salary_to * salary_to_coefficient
    return mean_salary


def fetch_vacancies_hh(url, language):
    moscow_id = 1
    days_to_parse = 30
    vacancies_per_page = 100
    payload = {
        'text': f'программист {language}',
        'area': moscow_id,
        'period': days_to_parse,
        'only_with_salary': True,
        'per_page': vacancies_per_page
    }
    for page in count():
        payload['page'] = page
        response = requests.get(url, params=payload)
        response.raise_for_status()
        vacancies_on_page = response.json()
        yield from vacancies_on_page['items']
        if page + 1 >= vacancies_on_page['pages']:
            break


def fetch_vacancies_sj(url, language, token):
    vacancies_per_page = 100
    header = {'X-Api-App-Id': token}
    payload = {
        'keyword': f'Программист {language}',
        'catalogues': 'Разработка, программирование',
        'town': 'Москва',
        'currency': 'rub',
        'count': vacancies_per_page,
    }
    for page in count():
        payload['page'] = page
        response = requests.get(url, params=payload, headers=header)
        response.raise_for_status()
        vacancies_on_page = response.json()
        yield from vacancies_on_page['objects']
        if not vacancies_on_page['more']:
            break


def get_table_content(vacancy_salaries, total_vacancies, language):
    vacancies_processed = len(vacancy_salaries)

    table_content = {
        'vacancies_found': total_vacancies,
        'vacancies_processed': vacancies_processed,
        'average_salary': None
    }
    if vacancy_salaries:
        mean_salary = mean(vacancy_salaries)
        table_content['average_salary'] = int(mean_salary)
    return table_content


def draw_table(table_content, title):
    header_row = [
        'Язык программирования',
        'Вакансий найдено',
        'Вакансий обработано',
        'Средняя зарплата'
    ]
    vacancies_table = [header_row]

    for language, language_vacancy in table_content.items():
        table_row = [
            language,
            language_vacancy['vacancies_found'],
            language_vacancy['vacancies_processed'],
            language_vacancy['average_salary']
        ]
        vacancies_table.append(table_row)

    table = AsciiTable(vacancies_table, title=title)
    return table.table


def get_sj_table_content(language):
    vacancy_salaries = []
    vacancies = fetch_vacancies_sj(sj_url, language, sj_token)

    for vacancy in vacancies:
        minimal_salary = vacancy['payment_from']
        maximal_salary = vacancy['payment_to']
        if salary := predict_salary(minimal_salary, maximal_salary):
            vacancy_salaries.append(salary)
    total_vacancies = fetch_sj_vacancies_number(sj_url, language, sj_token)
    table_content = get_table_content(
        vacancy_salaries, total_vacancies, language)
    return table_content


def get_hh_table_content(language):
    vacancy_salaries = []
    vacancies = fetch_vacancies_hh(hh_url, language)

    for vacancy in vacancies:
        salary_from, salary_to = get_salary_range_hh(vacancy)
        if salary := predict_salary(salary_from, salary_to):
            vacancy_salaries.append(salary)
    total_vacancies = fetch_hh_vacancies_number(hh_url, language)
    table_content = get_table_content(
        vacancy_salaries, total_vacancies, language)
    return table_content


def fetch_hh_vacancies_number(url, language):
    moscow_id = 1
    days_to_parse = 30
    payload = {
        'text': f'программист {language}',
        'area': moscow_id,
        'period': days_to_parse,
        'only_with_salary': True,
    }
    response = requests.get(url, params=payload)
    response.raise_for_status()
    return response.json()['found']


def fetch_sj_vacancies_number(url, language, token):
    header = {'X-Api-App-Id': token}
    payload = {
        'keyword': f'Программист {language}',
        'catalogues': 'Разработка, программирование',
        'town': 'Москва',
        'currency': 'rub',
    }
    response = requests.get(url, params=payload, headers=header)
    response.raise_for_status()
    return response.json()['total']


if __name__ == '__main__':
    logging.basicConfig(filename='job_parse.log', filemode='w')
    load_dotenv()
    sj_token = os.getenv('SUPERJOB_TOKEN')
    hh_url = 'https://api.hh.ru/vacancies'
    sj_url = 'https://api.superjob.ru/2.33/vacancies/'

    hh_table_content = {}
    sj_table_content = {}
    languages = [
        'Python',
        'Java',
        'JavaScript',
        'C#',
        'PHP',
        'C',
        'C++',
        'R',
        'Objective-C',
        'Swift',
        'TypeScript',
        'Matlab',
        'Kotlin',
        'Go',
        'Ruby',
        'VBA',
        'RUST',
        'Scala',
        'Visual Basic',
        'Ada',
        'Lua',
        ]

    for language in languages:
        try:
            sj_table_content[language] = get_sj_table_content(language)
        except (HTTPError, ConnectionError) as error:
            logging.exception(error)
        try:
            hh_table_content[language] = get_hh_table_content(language)
        except (HTTPError, ConnectionError) as error:
            logging.exception(error)

    print(draw_table(hh_table_content, 'HeadHunters'))
    print(draw_table(sj_table_content, 'SuperJob'))

import logging
import os
import requests

from dotenv import load_dotenv
from itertools import count
from requests.exceptions import (HTTPError, ConnectionError)
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
        return (salary_from + salary_to) / 2
    elif salary_from:
        return salary_from * salary_from_coefficient
    elif salary_to:
        return salary_to * salary_to_coefficient


def fetch_vacancies_hh(url, payload):
    for page in count():
        payload['page'] = page
        response = requests.get(url, params=payload)
        response.raise_for_status()

        yield response.json()['items'], response.json()['found']
        if page + 1 >= response.json()['pages']:
            break


def fetch_vacancies_sj(url, header, payload):
    for page in count():
        payload['page'] = page
        response = requests.get(url, params=payload, headers=header)
        response.raise_for_status()

        yield response.json()['objects'], response.json()['total']
        if not response.json()['more']:
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

    for language, language_statistics in table_content.items():
        table_row = [
            language,
            language_statistics['vacancies_found'],
            language_statistics['vacancies_processed'],
            language_statistics['average_salary']
        ]
        vacancies_table.append(table_row)

    table = AsciiTable(vacancies_table, title=title)
    return table.table


def get_sj_table_content(language, token):
    url = 'https://api.superjob.ru/2.33/vacancies/'

    vacancies_per_page = 100
    header = {'X-Api-App-Id': token}
    payload = {
        'keyword': f'Программист {language}',
        'catalogues': 'Разработка, программирование',
        'town': 'Москва',
        'currency': 'rub',
        'count': vacancies_per_page,
    }

    vacancy_salaries = []
    for page_of_response in fetch_vacancies_sj(url, header, payload):
        vacancies, total_vacancies = page_of_response
        for vacancy in vacancies:
            minimal_salary = vacancy['payment_from']
            maximal_salary = vacancy['payment_to']
            if salary := predict_salary(minimal_salary, maximal_salary):
                vacancy_salaries.append(salary)

    table_content = get_table_content(
        vacancy_salaries, total_vacancies, language)
    return table_content


def get_hh_table_content(language):
    url = 'https://api.hh.ru/vacancies'

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

    vacancy_salaries = []
    for page_of_response in fetch_vacancies_hh(url, payload):
        vacancies, total_vacancies = page_of_response
        for vacancy in vacancies:
            salary_from, salary_to = get_salary_range_hh(vacancy)
            if salary := predict_salary(salary_from, salary_to):
                vacancy_salaries.append(salary)

    table_content = get_table_content(
        vacancy_salaries, total_vacancies, language)
    return table_content


if __name__ == '__main__':
    logging.basicConfig(filename='job_parse.log', filemode='w')
    load_dotenv()
    sj_token = os.getenv('SUPERJOB_TOKEN')

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
            sj_table_content[language] = get_sj_table_content(language, sj_token)
        except (HTTPError, ConnectionError) as error:
            logging.exception(error)
        try:
            hh_table_content[language] = get_hh_table_content(language)
        except (HTTPError, ConnectionError) as error:
            logging.exception(error)

    print(draw_table(hh_table_content, 'HeadHunters'))
    print(draw_table(sj_table_content, 'SuperJob'))

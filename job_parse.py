import numpy
import os
import requests

from dotenv import load_dotenv
from itertools import count
from math import isnan
from terminaltables import AsciiTable


def get_salary_range_hh(vacancy):
    minimal_salary = vacancy['salary']['from']
    maximal_salary = vacancy['salary']['to']
    if vacancy['salary']['currency'] != 'RUR':
        minimal_salary, maximal_salary = None, None
    return minimal_salary, maximal_salary


def get_salary_range_sj(vacancy):
    minimal_salary = vacancy['payment_from']
    maximal_salary = vacancy['payment_to']
    return minimal_salary, maximal_salary


def predict_salary(salary_from, salary_to):
    salary_to_coefficient = 0.8
    salary_from_coefficient = 1.2
    if not salary_from and not salary_to:
        return None
    elif salary_from and salary_to:
        mean_salary = (salary_from + salary_to)/2
    elif not salary_from:
        mean_salary = salary_to * salary_to_coefficient
    elif not salary_to:
        mean_salary = salary_from * salary_from_coefficient
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


def get_language_vacancies(vacancy_salaries, total_vacancies, language):
    mean_salary = numpy.nanmean(numpy.array(vacancy_salaries, dtype=float))

    vacancies_processed = sum(1 for salary in vacancy_salaries if salary)
    language_vacancies = {
        'vacancies_found': total_vacancies,
        'vacancies_processed': vacancies_processed,
        'average_salary': None
    }
    if not isnan(mean_salary):
        language_vacancies['average_salary'] = int(mean_salary)
    return language_vacancies


def get_table(vacancies, title):
    header_row = [
        'Язык программирования',
        'Вакансий найдено',
        'Вакансий обработано',
        'Средняя зарплата'
        ]
    vacancies_table = [header_row]

    for language, language_vacancy in vacancies.items():
        table_row = [
            language,
            language_vacancy['vacancies_found'],
            language_vacancy['vacancies_processed'],
            language_vacancy['average_salary']]
        vacancies_table.append(table_row)

    table = AsciiTable(vacancies_table, title=title)
    return table.table


if __name__ == '__main__':
    load_dotenv()
    sj_token = os.getenv('SUPERJOB_TOKEN')
    hh_url = 'https://api.hh.ru/vacancies'
    sj_url = 'https://api.superjob.ru/2.33/vacancies/'

    hh_vacancies_for_language = {}
    sj_vacancies_for_language = {}
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
        sj_vacancy_salaries = []
        sj_vacancies = fetch_vacancies_sj(sj_url, language, sj_token)

        for vacancy in sj_vacancies:
            salary_from, salary_to = get_salary_range_sj(vacancy)
            salary = predict_salary(salary_from, salary_to)
            sj_vacancy_salaries.append(salary)
        sj_total_vacancies = len(sj_vacancy_salaries)
        sj_language_vacancies = get_language_vacancies(
            sj_vacancy_salaries, sj_total_vacancies, language
            )
        sj_vacancies_for_language[language] = sj_language_vacancies

        hh_vacancy_salaries = []
        hh_vacancies = fetch_vacancies_hh(hh_url, language)

        for vacancy in hh_vacancies:
            salary_from, salary_to = get_salary_range_hh(vacancy)
            salary = predict_salary(salary_from, salary_to)
            hh_vacancy_salaries.append(salary)
        hh_total_vacancies = len(hh_vacancy_salaries)
        hh_language_vacancies = get_language_vacancies(
            hh_vacancy_salaries, hh_total_vacancies, language
            )
        hh_vacancies_for_language[language] = hh_language_vacancies

    print(get_table(hh_vacancies_for_language, 'HeadHunters'))
    print(get_table(sj_vacancies_for_language, 'SuperJob'))

import numpy
import os
import requests

from dotenv import load_dotenv
from itertools import count
from math import isnan
from terminaltables import AsciiTable


def predict_rub_salary_hh(vacancy):
    if vacancy['salary']['currency'] != 'RUR':
        return None, None 
    minimal_salary = vacancy['salary']['from']
    maximal_salary = vacancy['salary']['to']
    return minimal_salary, maximal_salary 
    

def predict_rub_salary_sj(vacancy):
    if (minimal_salary := vacancy['payment_from']) == 0:
        minimal_salary = None
    if (maximal_salary := vacancy['payment_to']) == 0:
        maximal_salary = None
    return minimal_salary, maximal_salary


def predict_salary(salary_from, salary_to):
    if not salary_from and not salary_to:
        return None
    elif salary_from and salary_to:
        mean_salary = (salary_from + salary_to)/2
    elif not salary_from:
        mean_salary = salary_to * 0.8
    elif not salary_to:
        mean_salary = salary_from * 1.2
    return mean_salary


def fetch_vacancies_hh(url, language):
    for page in count():
        payload = {
            'text': f'программист {language}',
            'area': 1,
            'period': 30,
            'page': page,
            'only_with_salary': True,
            'per_page': 100
            }
        response = requests.get(url, params=payload)
        response.raise_for_status()
        page_data = response.json()
        # print(page_data)
        if page >= page_data['pages']:
            break
        yield from page_data['items']


def fetch_vacancies_sj(url, language):
    header = {'X-Api-App-Id': os.getenv('SUPERJOB_TOKEN')}
    for page in count():
        payload = {
            'keyword': f'Программист {language}',
            'catalogues': 'Разработка, программирование',
            'town': 'Москва',
            'currency': 'rub',
            'page': page,
            'count': 100,
            }
        response = requests.get(url, params=payload, headers=header)
        response.raise_for_status()
        page_data = response.json()
        if page >= page_data['total']:
            break
        yield from page_data['objects']


def get_vacancies_number_hh(url, language):
    payload = {
        'text': f'программист {language}',
        'area': 1,
        'period': 30,
        'only_with_salary': True,
        }
    response = requests.get(url, params=payload)
    response.raise_for_status()
    return response.json()['found']


# def get_vacancies_number_sj(url, language):
#     header = {'X-Api-App-Id': os.getenv('SUPERJOB_TOKEN')}
#     payload = {
#         'keyword': f'Программист {language}',
#         'catalogues': 'Разработка, программирование',
#         'town': 'Москва',
#         'currency': 'rub',
#         }
#     response = requests.get(url, params=payload, headers=header)
#     response.raise_for_status()
#     return response.json()['total']


def get_language_data(vacancy_salaries, total_vacancies, languages_info, language):
    mean_salary = numpy.nanmean(numpy.array(vacancy_salaries, dtype=float))

    vacancies_processed = sum(1 for salary in vacancy_salaries if salary)
    languages_info[language]['vacancies_found'] = total_vacancies
    languages_info[language]['vacancies_processed'] = vacancies_processed
    languages_info[language]['average_salary'] = None
    if not isnan(mean_salary):
        languages_info[language]['average_salary'] = int(mean_salary)
    return languages_info


def draw_table(vacancies_data, title):
    header_row = [
        'Язык программирования',
        'Вакансий найдено',
        'Вакансий обработано',
        'Средняя зарплата'
        ]
    table_data = [header_row]

    for language, language_data in vacancies_data.items():
        table_row = [
            language,
            language_data['vacancies_found'],
            language_data['vacancies_processed'],
            language_data['average_salary']]
        table_data.append(table_row)
        
    table = AsciiTable(table_data, title=title)
    print(table.table)


if __name__ == '__main__':
    load_dotenv()
    hh_url = 'https://api.hh.ru/vacancies'
    sj_url = 'https://api.superjob.ru/2.33/vacancies/'
    
    hh_languages_info = {}
    sj_languages_info = {}
    languages = [
    'JavaScript',
    'Java',
    # 'C#',
    # 'Python',
    # 'PHP',
    # 'TypeScript',
    # 'C++',
    # 'Swift',
    # 'Ruby',
    # 'Kotlin',
    # 'Go',
    # 'Scala',
    # 'C',
    # '1C',
    # 'T-SQL',
    # 'Dart',
    # 'PL-SQL',
    # 'Pascal/Delphi',
    'R',
    'Apex'
    ]


    for language in languages:
        sj_languages_info[language] = {}
        sj_vacancy_salaries = []
        sj_vacancies = fetch_vacancies_sj(sj_url, language)

        for vacancy in sj_vacancies:
            salary_from, salary_to = predict_rub_salary_sj(vacancy)
            salary = predict_salary(salary_from, salary_to)
            sj_vacancy_salaries.append(salary)
        # print(sj_vacancy_salaries)
        sj_total_vacancies = len(sj_vacancy_salaries)
        get_language_data(sj_vacancy_salaries, sj_total_vacancies, sj_languages_info, language)

        hh_languages_info[language] = {}
        hh_vacancy_salaries = []
        hh_vacancies = fetch_vacancies_hh(hh_url, language)

        for vacancy in hh_vacancies:
            salary_from, salary_to = predict_rub_salary_hh(vacancy)
            print(salary_from, salary_to)
            salary = predict_salary(salary_from, salary_to)
            hh_vacancy_salaries.append(salary)
        # print(hh_vacancy_salaries)
        hh_total_vacancies = len(hh_vacancy_salaries)
        get_language_data(hh_vacancy_salaries, hh_total_vacancies, hh_languages_info, language)

    
    # print(hh_languages_info)
    # print(sj_languages_info)
    
    
        # table_data.extend([language, ])
    # print(table_data)
    
    draw_table(hh_languages_info, 'HeadHunters')
    draw_table(sj_languages_info, 'SuperJob')


import numpy
import requests

from itertools import count


def predict_rub_salary(vacancy):
    vacancy_currency = vacancy['salary']['currency']
    minimal_salary = vacancy['salary']['from']
    maximal_salary = vacancy['salary']['to']
    if vacancy_currency != 'RUR':
        return None
    elif minimal_salary and maximal_salary:
        mean_salary = (minimal_salary + maximal_salary)/2
    elif not minimal_salary:
        mean_salary = maximal_salary * 0.8
    elif not maximal_salary:
        mean_salary = minimal_salary * 1.2
    return mean_salary


def fetch_vacancies(url, language):
    for page in count():
        payload = {
            'text': f'программист {language}',
            'area': 1,
            'period': 30,
            'only_with_salary': True,
            'page': page,
            'per_page': 100
            }
        response = requests.get(url, params=payload)
        response.raise_for_status()
        page_data = response.json()
        if page >= page_data['pages']:
            break
        yield from page_data['items']


def get_vacancies_number(url, language):
    payload = {
        'text': f'программист {language}',
        'area': 1,
        'period': 30,
        'only_with_salary': True,
        }
    response = requests.get(url, params=payload)
    response.raise_for_status()
    return response.json()['found']


if __name__ == '__main__':
    hh_url = 'https://api.hh.ru/vacancies'
    languages_info = {}

    languages = [
    'JavaScript',
    'Java',
    'C#',
    'Python',
    'PHP',
    'TypeScript',
    'C++',
    'Swift',
    'Ruby',
    'Kotlin',
    'Go',
    'Scala',
    'C',
    '1C',
    'T-SQL',
    'Dart',
    'PL-SQL',
    'Pascal/Delphi',
    'R',
    'Apex'
    ]

    for language in languages:
        languages_info[language] = {}

        vacancies = fetch_vacancies(hh_url, language)

        vacancy_salaries = [predict_rub_salary(vacancy) for vacancy in vacancies]
        mean_salary = numpy.nanmean(numpy.array(vacancy_salaries, dtype=float))

        vacancies_processed = sum(1 for salary in vacancy_salaries if salary)
        languages_info[language]['vacancies_found'] = get_vacancies_number(hh_url, language)
        languages_info[language]['vacancies_processed'] = vacancies_processed
        languages_info[language]['average_salary'] = int(mean_salary)

    print(languages_info) 

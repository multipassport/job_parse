# Сравниваем вакансии программистов

Скрипт показывает средние зарплаты и количество вакансий в Москве по каждому из языков программирования из топа по версии [Хабра](https://habr.com/ru/company/skillfactory/blog/531360/). Информация о вакансиях взята с сайтов [HeadHunters.ru](https://dev.hh.ru/) и [SuperJob.ru](https://api.superjob.ru/).

### Как запустить

Для запуска скрипта необходим установленный Python 3.

Скачайте код с GitHub, а затем установите зависимости командой:

```bash
pip install -r requirements.txt
```

Создайте файл `.env` рядом с job_parse.py, в котором должно быть:

```SUPERJOB_TOKEN``` - Secret Key приложения [Superjob](https://api.superjob.ru/info/).

Запустите скрипт:

```bash
python job_parse.py
```

### Результат

![Screenshot](https://user-images.githubusercontent.com/80415662/118800524-aeb44b80-b8a8-11eb-9f55-91e23c364f25.png)

### Цель проекта

Код написан в образовательных целях на онлайн-курсе для веб-разработчиков [dvmn.org](https://dvmn.org/).

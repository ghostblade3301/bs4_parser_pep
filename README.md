# Проект парсинга pep

### Описание
Проект для парсинга документации Python.
В проекте настроено логирование, а также обработка исключений.

### Технологии
- Python 3.10.6

### Настройка
Создайте и активируйте виртуальное окружение, обновите менеджер пакетов pip и установите зависимости из файла requirements.txt.
```
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Режимы работы
Запуск парсера для обработки статей с нововведениями
```
python main.py whats-new
```
Запуск парсера для получение информации о последних версиях
```
python main.py latest-versions
```
Запуск парсера, для скачивания архива с документацией
```
python main.py download
```
Запуск парсера для поиска текущих статусов PEP
```
python main.py pep
```

### Аргументы командной строки
Список аргументов командной строки можно получить введя команду:
```
python main.py -h
```
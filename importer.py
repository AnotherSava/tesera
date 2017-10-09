import csv
import urllib.request

import pandas
from bs4 import BeautifulSoup
from pandas import DataFrame
from ast import literal_eval

URL_PREFIX = "http://tesera.ru"

COLUMN_URL_FULL = 'url_full'
COLUMN_URL_SHORT = 'url'
COLUMN_NAME = 'name'
COLUMN_NAME_MAIN = 'name_main'
COLUMN_NAME_OTHER = 'name_other'
COLUMN_OWNERS = 'owners'
COLUMN_OWNERS_LIST = 'owners_list'

FILE_NAME = 'data.csv'
FILE_NAME_BACKUP = 'data.backup.csv'
ENCODING = 'utf-16'


def write_file():
    try:
        data.to_csv(FILE_NAME, index_label=COLUMN_URL_SHORT, encoding=ENCODING)
    except:
        print("ERROR: File '" + FILE_NAME + "' is locked, using '" + FILE_NAME_BACKUP + "' instead")
        data.to_csv(FILE_NAME_BACKUP, index_label=COLUMN_URL_SHORT, encoding=ENCODING)


def read_file():
    global data
    data = pandas.read_csv(FILE_NAME, index_col=COLUMN_URL_SHORT, encoding=ENCODING, converters={COLUMN_OWNERS_LIST: literal_eval})
    set_data_types()


# На русском ли языке строка
def is_russian(str):
    for c in str:
        if 'а' <= c <= 'я' or 'А' <= c <= 'Я':
            return True
    return False


# На основании полей основного и дополнительных названий Тесеры сторим своё красивое название игры
def create_name(name_main, name_other):
    if len(name_other) < 1:
        return name_main

    if len(name_other) == 4 and name_other.isdigit():
        return name_main

    name_other_first = name_other.split(',')[0].strip()

    if is_russian(name_other_first):
        return name_main

    if not is_russian(name_main):
        return name_main

    return name_other_first


# Заполняем столбец красивого имени на основании столбцов основного и дополнительных названий с Тесеры
def parse_names():
    for row in data.iterrows():
        game_url = row[0]
        name_main = row[1][COLUMN_NAME_MAIN].strip()
        name_other = row[1][COLUMN_NAME_OTHER].strip()
        data.set_value(game_url, COLUMN_NAME, create_name(name_main, name_other))


# Заполняем столбец ссылок на игру на основе относительных ссылок, которые у нас используются в качестве индекса
def parse_urls():
    for row in data.iterrows():
        game_url = row[0]
        data.set_value(game_url, COLUMN_URL_FULL, URL_PREFIX + game_url)


# Из списка владельцев делаем строку
def parse_owners():
    for row in data.iterrows():
        game_url = row[0]
        owners_string = ""
        owners_list = data.get_value(game_url, COLUMN_OWNERS_LIST)
#            row[1][COLUMN_OWNERS_LIST]

#             owners = data.get_value(link, COLUMN_OWNERS_LIST)
#             owners.append(username)
#             data.set_value(link, COLUMN_OWNERS_LIST, owners)

        if len(owners_list) > 1:
            for owner in sorted(owners_list):
                if len(owners_string) > 0:
                    owners_string += ", "
                owners_string += owner
        else:
            owners_string = row[1][COLUMN_OWNERS_LIST][0]

        data.set_value(game_url, COLUMN_OWNERS, owners_string)


# Для каждой игры берём ссылку на неё, идём по этой ссылке, получаем поля основного и дополнительного названий и заполняем их
def update_names():
    length = len(data)
    for row in data.iterrows():
        print('Records to go: ' + str(length))

        game_url = row[0]
        connection = urllib.request.urlopen(URL_PREFIX + game_url)
        response = connection.read()
        connection.close()
        soup = BeautifulSoup(response, "html.parser")
        game_record = soup.find_all('div', attrs={'class': 'leftcol'})[0]
        full_name = game_record.find('h1').find('span').contents[0]
        original_name = game_record.find('h3').contents[0]
        data.loc[game_url, COLUMN_NAME_MAIN] = full_name
        data.loc[game_url, COLUMN_NAME_OTHER] = original_name

        length -= 1

# Загружаем список игр пользователя. Если игра уже есть в списке, добавляем нового владельца, иначе добавляем в список.
def add_games(username):
    url = URL_PREFIX + "/user/" + username + "/games/owns/all"
    connection = urllib.request.urlopen(url)
    response = connection.read()
    connection.close()

    soup = BeautifulSoup(response, "html.parser")
    games = soup.findAll('div', attrs={'class': 'gameslinked'})

    for game in games:
        link = game.find('div', attrs={'class': 'text'}).find('a')['href']
        if link in data.index.values:
            # data.loc[link, COLUMN_OWNERS] = data[link][COLUMN_OWNERS] + " " + username
            owners = data.get_value(link, COLUMN_OWNERS_LIST)
            owners.append(username)
            data.set_value(link, COLUMN_OWNERS_LIST, owners)
        else:
            data.loc[link, COLUMN_OWNERS_LIST] = [username]


# Вся информация об играх, умеем записывать/считывать её из файла, дополнять с тесеры и обрабатывать уже имеющиеся данные
data = DataFrame(columns=(COLUMN_NAME, COLUMN_NAME_MAIN, COLUMN_NAME_OTHER, COLUMN_OWNERS_LIST, COLUMN_OWNERS, COLUMN_URL_FULL))


def set_data_types():
    data[[COLUMN_NAME]] = data[[COLUMN_NAME]].astype(str)                   # название, которое больше нравится мне (производное поле)
    data[[COLUMN_NAME_MAIN]] = data[[COLUMN_NAME_MAIN]].astype(str)         # "основное название" с Тесеры
    data[[COLUMN_NAME_OTHER]] = data[[COLUMN_NAME_OTHER]].astype(str)       # "дополнительные названия" с Тесеры
    data[[COLUMN_OWNERS_LIST]] = data[[COLUMN_OWNERS_LIST]].astype(object)  # все владельцы списком
    data[[COLUMN_OWNERS]] = data[[COLUMN_OWNERS]].astype(str)               # все владельцы строкой
    data[[COLUMN_URL_FULL]] = data[[COLUMN_URL_FULL]].astype(str)           # ссылка на профиль игры на Тесере


set_data_types()

# считывать начальные данные из файла или из профилей Тесеры
online = False

user_list = ["tigronok", "janlynn", "tatafrost", "bobrik", "anothersava", "eugene0", "ArranHawk", "Caleb", "Oxma", "x_master05", "vyatskiy", "ayouk", "ksedih", "Rapait", "Fox", "igelkott"]

if online:
    for user in user_list:
        print("Loaging games list for: " + user)
        add_games(user)
else:
    read_file()

# Для каждой игры берём ссылку на неё, идём по этой ссылке, получаем поля основного и дополнительного названий и заполняем их
#update_names()

# Заполняем столбец красивого имени на основании столбцов основного и дополнительных названий с Тесеры
#parse_names()

# Заполняем столбец ссылок на игру на основе относительных ссылок, которые у нас используются в качестве индекса
#parse_urls()

# Из списка владельцев делаем строку
parse_owners()

write_file()
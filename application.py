import importer

users = [line.rstrip('\n') for line in open('users_test.txt', 'r')]

# считывать начальные данные из файла или из профилей Тесеры
online = True

if online:
    data = importer.create_empty_dataframe()
    for user in users:
        print("Loaging games list for: " + user)
        importer.add_games(data, user)
else:
    data = importer.read_file()

# Из списка владельцев делаем строку
# importer.parse_owners(data)

# Для каждой игры берём ссылку на неё, идём по этой ссылке, получаем поля основного и дополнительного названий и заполняем их
importer.update_names(data)

importer.write_file(data)

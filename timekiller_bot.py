# -*- coding: utf-8 -*-
import json
from telebot import types
import config
import telebot
import random
import logging
import psycopg2

logging.basicConfig(filename="logger/timekiller_bot.log", level=logging.INFO)
bot = telebot.TeleBot(config.token_timekiller_bot)


def total_count_of_score_on_field(count_end) -> int:
    """
    Подсчет количества очков после завершения игры.
    :param count_end: Поле после окончания игры
    :return: (int) количество очков на поле
    """
    score_now = 0
    for i in range(4):
        for j in range(4):
            score_now += count_end[i][j]
    return score_now


def final_2048(message, score_now):
    """
    Обнуление значений на поле, вывод сообщеня о завершении игры и количества набранных очков.
    :param message: (JSON) сообщение от пользователя
    :param score_now: Количество очков в этой игре
    :return: (int) количество очков на поле
    """
    with open('params.json', 'r') as f:
        load_json = json.load(f)
    with open('params.json', 'w') as f:
        load_json.update({str(message.chat.id): {
            'game_2048': add_element(config.new_field),
            'username': message.chat.username, 'first_name': message.chat.first_name,
            'last_name': message.chat.last_name,
            'top_score': max(score_now[0], load_json[str(message.chat.id)]['top_score'])}})
        json.dump(load_json, f, indent=2)
        logging.info("User {uname} lose game: 2048 | score: {score}.".format(uname=message.chat.username,
                                                                             score=str(score_now[0])))
        bot.send_message(message.chat.id,
                         "💢  GAME OVER  💢\nYour score now: " + str(score_now[0]) + "!\nYour top score:" + str(max(
                             score_now[0], load_json[str(message.chat.id)]['top_score'])),
                         reply_markup=update_keyboard_2048(score_now))


def add_element(ae):
    """
    Проверка поля на возможность добавить и объединить элементы.
    1) Если есть свободное место добавляет в случайное пустое поле 2 или 4 (4 с вероятностью 10%);
    2) Если мета нет проверяет можно ли объединить какие-либо клетки
    (ячейки по вертикали или горизонтали имеют одно значение);
    3) Если это невозможно - игра завершена: подсчитывается общее кол-во очков.
    :param ae: Игровое поле пользователя
    :return: 1) Поле с новым значением в пустом месте; 2)  3) ['кол-во очков', 'end_game']
    """
    zero_points = [[], []]  # Хранит координаты клеток, значения которых равны 0
    merge = 0  # Хранит количество возможных объединений
    for i in range(4):
        for j in range(4):
            if ae[i][j] == 0:
                zero_points[0].append(i)
                zero_points[1].append(j)
            if 0 < j < 3:
                if ae[i][j] == ae[i][j - 1] or ae[i][j] == ae[i][j + 1]:
                    merge += 1
            if 0 < i < 3:
                if ae[i - 1][j] == ae[i][j] or ae[i + 1][j] == ae[i][j]:
                    merge += 1
    if len(zero_points[0]) == 1 and merge == 0:
        i = random.randint(0, len(zero_points[0]) - 1)
        ae[zero_points[0][i]][zero_points[1][i]] = 4 if random.randint(1, 10) == 7 else 2
        return add_element(ae)
    if len(zero_points[0]) == 0 and merge == 0:
        temp = total_count_of_score_on_field(ae) + (4 if random.randint(1, 10) == 7 else 2)
        return [temp, 'end_game']
    else:
        if len(zero_points[0]) != 0:
            i = random.randint(0, len(zero_points[0]) - 1)
            ae[zero_points[0][i]][zero_points[1][i]] = 4 if random.randint(1, 10) == 7 else 2
        return ae


def swap_all(game_2048, move_to):
    """
    Выполняет перестановку поля так, чтобы выполнять сдвиг и слияние влево и вернуть все назад.
    :param move_to: Необходимое действие с полем
    :param game_2048: Игровое поле
    :return: Поле в результате перестановок
    """
    if move_to == "move_right":
        game_2048[0][0], game_2048[0][3] = game_2048[0][3], game_2048[0][0]
        game_2048[0][1], game_2048[0][2] = game_2048[0][2], game_2048[0][1]
        game_2048[1][0], game_2048[1][3] = game_2048[1][3], game_2048[1][0]
        game_2048[1][1], game_2048[1][2] = game_2048[1][2], game_2048[1][1]
        game_2048[2][0], game_2048[2][3] = game_2048[2][3], game_2048[2][0]
        game_2048[2][1], game_2048[2][2] = game_2048[2][2], game_2048[2][1]
        game_2048[3][0], game_2048[3][3] = game_2048[3][3], game_2048[3][0]
        game_2048[3][1], game_2048[3][2] = game_2048[3][2], game_2048[3][1]
        return game_2048

    invert = [[0, 0, 0, 0],
              [0, 0, 0, 0],
              [0, 0, 0, 0],
              [0, 0, 0, 0]]

    if move_to == "move_up":
        for j in range(4):
            for i in range(4):
                invert[j][i] = game_2048[i][j]
        return invert

    if move_to == "move_down_to":
        for j in range(3, -1, -1):
            for i in range(3, -1, -1):
                invert[3 - j][3 - i] = game_2048[i][j]
        return invert

    if move_to == "move_down_back":
        for j in range(3, -1, -1):
            for i in range(3, -1, -1):
                invert[3 - i][3 - j] = game_2048[j][i]
        return invert


def permutation(game_2048):
    """
    Выполняет сдвиг и слияние всех клеток на поле влево.
    Если не удалось сдвинуть ни одну клетку - возврящает поле, все значения которого равны -1.
    :param game_2048: Игровое поле
    :return: Получившееся игровое поле
    """
    skip_move = -1
    for i in range(4):
        for j in range(1, 4):
            if game_2048[i][j] == 0 | (
                    game_2048[i][j - 1] != game_2048[i][j] and game_2048[i][j] != 0 and game_2048[i][j - 1] != 0):
                continue
            count = 1
            while (game_2048[i][j - count - 1] == 0 and j > count) or (
                    game_2048[i][j - count - 1] == game_2048[i][j] and j > count and game_2048[i][j - count] == 0):
                count += 1
            if game_2048[i][j - count] == 0:
                game_2048[i][j - count], game_2048[i][j] = game_2048[i][j], game_2048[i][j - count]
                skip_move += 1
            if game_2048[i][j - count] == game_2048[i][j] and game_2048[i][j] != 0:
                game_2048[i][j - count] *= 2
                game_2048[i][j] = 0
                skip_move += 1
                if j == 1:
                    game_2048[i][1], game_2048[i][2] = game_2048[i][2], game_2048[i][1]
                    game_2048[i][2], game_2048[i][3] = game_2048[i][3], game_2048[i][2]
                if j == 2:
                    game_2048[i][2], game_2048[i][3] = game_2048[i][3], game_2048[i][2]
    if skip_move == -1:
        game_2048 = [[-1, -1, -1, -1],
                     [-1, -1, -1, -1],
                     [-1, -1, -1, -1],
                     [-1, -1, -1, -1]]
    return game_2048


def update_keyboard_2048(game_2048):
    if game_2048[1] == 'end_game':
        keyboard = types.ReplyKeyboardMarkup(row_width=1)
        btn = types.KeyboardButton("2️⃣ 0️⃣ 4️⃣ 8️⃣")
        keyboard.add(btn)
    else:
        keyboard = types.ReplyKeyboardMarkup(row_width=4)
        btn00 = types.KeyboardButton(game_2048[0][0])
        btn01 = types.KeyboardButton(game_2048[0][1])
        btn02 = types.KeyboardButton(game_2048[0][2])
        btn03 = types.KeyboardButton(game_2048[0][3])
        btn10 = types.KeyboardButton(game_2048[1][0])
        btn11 = types.KeyboardButton(game_2048[1][1])
        btn12 = types.KeyboardButton(game_2048[1][2])
        btn13 = types.KeyboardButton(game_2048[1][3])
        btn20 = types.KeyboardButton(game_2048[2][0])
        btn21 = types.KeyboardButton(game_2048[2][1])
        btn22 = types.KeyboardButton(game_2048[2][2])
        btn23 = types.KeyboardButton(game_2048[2][3])
        btn30 = types.KeyboardButton(game_2048[3][0])
        btn31 = types.KeyboardButton(game_2048[3][1])
        btn32 = types.KeyboardButton(game_2048[3][2])
        btn33 = types.KeyboardButton(game_2048[3][3])
        btn_left = types.KeyboardButton("⬅️")
        btn_up = types.KeyboardButton("⬆️")
        btn_down = types.KeyboardButton("⬇️")
        btn_right = types.KeyboardButton("➡️")

        keyboard.add(btn00, btn01, btn02, btn03)
        keyboard.add(btn10, btn11, btn12, btn13)
        keyboard.add(btn20, btn21, btn22, btn23)
        keyboard.add(btn30, btn31, btn32, btn33)
        keyboard.add(btn_left, btn_up, btn_down, btn_right)
    return keyboard


@bot.message_handler(commands=['start'])
def start(message):
    logging.info("User {uname} [{fn} {ln}] start bot.".format(uname=message.chat.username, fn=message.chat.first_name,
                                                              ln=message.chat.last_name))
    keyboard = types.ReplyKeyboardMarkup(row_width=4)
    btn1 = types.KeyboardButton("2️⃣ 0️⃣ 4️⃣ 8️⃣")
    keyboard.add(btn1)
    with open('params.json', 'r') as f:
        load_json = json.load(f)
    with open('params.json', 'w') as f:
        load_json.update({str(message.chat.id): {'game_2048': config.new_field,
                                                 'username': message.chat.username,
                                                 'first_name': message.chat.first_name,
                                                 'last_name': message.chat.last_name, 'top_score': 0}})
        json.dump(load_json, f, indent=2)

    bot.send_message(message.chat.id,
                     "Settle down, relax and get comfy because you, my friend... are going nowhere.\n"
                     + "How about we play one more game, " + message.chat.first_name + "?",
                     reply_markup=keyboard)


@bot.message_handler(content_types=['text'])
def find_text(message):
    if message.text == '2️⃣ 0️⃣ 4️⃣ 8️⃣':
        logging.info("User {uname} start 2048.".format(uname=message.chat.username))
        with open('params.json', 'r') as f:
            load_json = json.load(f)
        with open('params.json', 'w') as f:
            load_json.update({str(message.chat.id): {
                'game_2048': add_element(config.new_field),
                'username': message.chat.username, 'first_name': message.chat.first_name,
                'last_name': message.chat.last_name, 'top_score': load_json[str(message.chat.id)]['top_score']}})
            json.dump(load_json, f, indent=2)

        with open('params.json', 'r') as f:
            load_json = json.load(f)
        bot.send_message(message.chat.id,
                         "Let's start the game! \n2️⃣ 0️⃣ 4️⃣ 8️⃣\n📜Rules:\n "
                         "You have to combine various tiles starting with a tile of 2 and combining them "
                         "together to reach 2048. The combinations include combining \'2\' tile with \'2\' "
                         "tile to make it into a tile of \'4\' and then combining it with a tile of \'4\' "
                         "to make a tile of \'8\' and so on.\nPress the corresponding arrows on the custom keyboard"
                         " and set a new record!",
                         reply_markup=update_keyboard_2048(load_json[str(message.chat.id)]['game_2048']))

    elif message.text == '⬅️':
        with open('params.json', 'r') as f:
            load_json = json.load(f)
        game_2048 = permutation(load_json[str(message.chat.id)]['game_2048'])

        if game_2048[0][0] == -1:
            game_2048 = load_json[str(message.chat.id)]['game_2048']
            text = "NOPE\n🤛🏼😈🤜🏼"
        else:
            game_2048 = add_element(game_2048)
            text = "⬅ Move left ⬅"

        if game_2048[1] == 'end_game':
            final_2048(message, game_2048)
        else:
            with open('params.json', 'r') as f:
                load_json = json.load(f)
            with open('params.json', 'w') as f:
                load_json.update({str(message.chat.id): {
                    'game_2048': game_2048,
                    'username': message.chat.username, 'first_name': message.chat.first_name,
                    'last_name': message.chat.last_name, 'top_score': load_json[str(message.chat.id)]['top_score']}})
                json.dump(load_json, f, indent=2)

            game_2048 = update_keyboard_2048(game_2048)
            bot.send_message(message.chat.id, text, reply_markup=game_2048)

    elif message.text == '⬇️':
        with open('params.json', 'r') as f:
            load_json = json.load(f)
        game_2048 = swap_all(permutation(swap_all(load_json[str(message.chat.id)]['game_2048'], "move_down_to")),
                             "move_down_back")

        if game_2048[0][0] == -1:
            game_2048 = load_json[str(message.chat.id)]['game_2048']
            text = "NOPE\n🤛🏼😈🤜🏼"
        else:
            game_2048 = add_element(game_2048)
            text = "⬇ Move down ⬇"

        if game_2048[1] == 'end_game':
            final_2048(message, game_2048)
        else:
            with open('params.json', 'r') as f:
                load_json = json.load(f)
            with open('params.json', 'w') as f:
                load_json.update({str(message.chat.id): {
                    'game_2048': game_2048,
                    'username': message.chat.username, 'first_name': message.chat.first_name,
                    'last_name': message.chat.last_name, 'top_score': load_json[str(message.chat.id)]['top_score']}})
                json.dump(load_json, f, indent=2)

            game_2048 = update_keyboard_2048(game_2048)
            bot.send_message(message.chat.id, text, reply_markup=game_2048)

    elif message.text == '⬆️':
        with open('params.json', 'r') as f:
            load_json = json.load(f)
        game_2048 = swap_all(permutation(swap_all(load_json[str(message.chat.id)]['game_2048'], "move_up")), "move_up")

        if game_2048[0][0] == -1:
            game_2048 = load_json[str(message.chat.id)]['game_2048']
            text = "NOPE\n🤛🏼😈🤜🏼"
        else:
            game_2048 = add_element(game_2048)
            text = "⬆️ Move up ⬆️"

        if game_2048[1] == 'end_game':
            final_2048(message, game_2048)
        else:
            with open('params.json', 'r') as f:
                load_json = json.load(f)
            with open('params.json', 'w') as f:
                load_json.update({str(message.chat.id): {
                    'game_2048': game_2048,
                    'username': message.chat.username, 'first_name': message.chat.first_name,
                    'last_name': message.chat.last_name, 'top_score': load_json[str(message.chat.id)]['top_score']}})
                json.dump(load_json, f, indent=2)

            game_2048 = update_keyboard_2048(game_2048)
            bot.send_message(message.chat.id, text, reply_markup=game_2048)

    elif message.text == '➡️':
        with open('params.json', 'r') as f:
            load_json = json.load(f)
        game_2048 = permutation(swap_all(load_json[str(message.chat.id)]['game_2048'], "move_right"))
        if game_2048[0][0] == -1:
            game_2048 = swap_all(load_json[str(message.chat.id)]['game_2048'], "move_right")
            text = "NOPE\n🤛🏼😈🤜🏼"
        else:
            game_2048 = add_element(swap_all(game_2048, "move_right"))
            text = "➡ Move right ➡"

        if game_2048[1] == 'end_game':
            final_2048(message, game_2048)
        else:
            with open('params.json', 'r') as f:
                load_json = json.load(f)
            with open('params.json', 'w') as f:
                load_json.update({str(message.chat.id): {
                    'game_2048': game_2048,
                    'username': message.chat.username, 'first_name': message.chat.first_name,
                    'last_name': message.chat.last_name, 'top_score': load_json[str(message.chat.id)]['top_score']}})
                json.dump(load_json, f, indent=2)

            game_2048 = update_keyboard_2048(game_2048)
            bot.send_message(message.chat.id, text,
                             reply_markup=game_2048)

    elif message.text == '0' or message.text == '2' or message.text == '4' or message.text == '8' \
            or message.text == '16' or message.text == '32' or message.text == '64' or message.text == '128' \
            or message.text == '256' or message.text == '512' or message.text == '1024' or message.text == '2048' \
            or message.text == '4096':
        with open('params.json', 'r') as f:
            load_json = json.load(f)
        bot.send_message(message.chat.id, "I appeal to you to leave the numbers unchanged.",
                         reply_markup=update_keyboard_2048(load_json[str(message.chat.id)]['game_2048']))
    else:
        with open('params.json', 'r') as f:
            load_json = json.load(f)
        bot.send_message(message.chat.id,
                         "To be honest, I don't understand the reasons for such actions...\n"
                         "Don't write to me anymore. JUST PLAY!",
                         reply_markup=update_keyboard_2048(load_json[str(message.chat.id)]['game_2048']))


bot.polling()

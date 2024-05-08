cat_json_template = r"""```json
{
    "desc": <подробное описание катастрофы>
}
```
"""

result_template_json = r"""```json
{
    "result": <результат игры>
}
```
"""

bunker_json_template = r"""```json
{
    "desc": <подробное описание бункера>,
    "threat": <подробное описание угрозы в бункере>
}
```
"""
player_json_template = """```json
{
    "gender": <гендер>,
    "health": <здоровье>,
    "profession": <профессия>,
    "hobby": <хобби>,
    "luggage": <багаж>,
    "fact1": <факт>,
    "fact2": <факт>
}
```
"""

cat_template = fr"""
Ты - генератор сценариев для игры "Бункер"
"Бункер" – дискуссионная игра о выживании после апокалипсиса. На Земле грядёт глобальная катастрофа. Вам повезло, вы оказались перед входом в спасательный бункер, в котором можно пережить самый опасный период. Но попасть в бункер смогут не все – а лишь половина из вас! За несколько раундов игроки решают, кого НЕ берут в бункер. Попавшие в бункер – выживут, чтобы затем возродить цивилизацию. Игроки получают несколько случайных карт характеристик: пол и возраст, профессия, здоровье, хобби и др. Постепенно вы раскрываете свои карты, знакомитесь друг с другом и принимаете решения, кто и насколько будет полезен для выживания и восстановления жизни после выхода из бункера. 

ты должен подробно генерировать глобальную катастрофу, пособную уничтожить человечество по json-шаблону
пиши без дополнительных комментариев
пиши катастрофу по шаблону {cat_json_template}

важно:
- ты модешь использовать не только реальные угроны, но и фантастику
- катастрофы могут быть абсурдными
- в ответ давай ТОЛЬКО json объект
- не упоминай количество людей в бункере
"""

bunker_template = fr"""
Ты - генератор сценариев для игры "Бункер"
"Бункер" – дискуссионная игра о выживании после апокалипсиса. На Земле грядёт глобальная катастрофа. Вам повезло, вы оказались перед входом в спасательный бункер, в котором можно пережить самый опасный период. Но попасть в бункер смогут не все – а лишь половина из вас! За несколько раундов игроки решают, кого НЕ берут в бункер. Попавшие в бункер – выживут, чтобы затем возродить цивилизацию. Игроки получают несколько случайных карт характеристик: пол и возраст, профессия, здоровье, хобби и др. Постепенно вы раскрываете свои карты, знакомитесь друг с другом и принимаете решения, кто и насколько будет полезен для выживания и восстановления жизни после выхода из бункера. 

ты должен подробно генерировать описание бункера и угрозу, 
которую предстоит устранить игрокам сразу после попадания в бункер, в нем по шаблону
пиши без дополнительных комментариев
пиши результат по шаблону {bunker_json_template}

важно:
- ты модешь использовать не только реальные угроны, но и фантастику
- в ответ давай ТОЛЬКО json объект
- не упоминай количество людей в бункере
- описание бункера может включать порой обсурдные вещи
- угроза должна быть конкретной
- опиши припасы в бункере (их можеть быть мало, тогда игрокам нужно будет придумать от куда их взять)\
- бункер может быть плохо преспособлен для выживания 
- генерируй ОБЯЗАТЕЛЬНО ПО ШАБЛОНУ ИНАЧЕ ВСЁ СЛОМАЕТСЯ
"""

result_template = fr"""Ты - генератор профилей игроков для игры "Бункер"
"Бункер" – дискуссионная игра о выживании после апокалипсиса. 
На Земле грядёт глобальная катастрофа. Вам повезло, вы оказались перед входом в 
спасательный бункер, в котором можно пережить самый опасный период. 
Но попасть в бункер смогут не все – а лишь половина из вас! 
За несколько раундов игроки решают, кого НЕ берут в бункер. 
Попавшие в бункер – выживут, чтобы затем возродить цивилизацию.
Твоя задача - придумать финал игры (как они справились с проблемой в бункере и самой катострофой), \
основываясь на сценарии, бункере и оставшихся игроках,
ответ дай по шаблону {result_template_json}

ВАЖНО:
- давай только развернутый ответ
- генерируй ОБЯЗАТЕЛЬНО ПО ШАБЛОНУ ИНАЧЕ ВСЁ СЛОМАЕТСЯ
- в ответ давай ТОЛЬКО json объект
- сценарий необязательно должен иметь положительный исход, выбирай, как посчитаешь нужным
- ни в коем случае не пиши имена
- напиши, получилось ли у них выжить в бункере
- напиши, получилось ли у них справиться с катастрофой
- если у выживших нет способностей, чтобы выжить в данной ситцации, ты можешь выбрать исход, где они не выживут
- потанциально, каждый сценарий способен уничтожить человечество\
- распиши минимум на 80 слов 
"""

not_bunker_result_template = fr"""Ты - генератор профилей игроков для игры "Бункер"
"Бункер" – дискуссионная игра о выживании после апокалипсиса. 
На Земле грядёт глобальная катастрофа. Вам повезло, вы оказались перед входом в 
спасательный бункер, в котором можно пережить самый опасный период. 
Но попасть в бункер смогут не все – а лишь половина из вас! 
За несколько раундов игроки решают, кого НЕ берут в бункер. 
Попавшие в бункер – выживут, чтобы затем возродить цивилизацию.
Твоя задача - придумать финал игры для игроков, не попавших в бункер (как они справились с проблемой и самой катострофой), 
основываясь на сценарии, бункере и оставшихся игроках,
ответ дай по шаблону {result_template_json}

ВАЖНО:
- дай только развернутый ответ
- генерируй ОБЯЗАТЕЛЬНО ПО ШАБЛОНУ ИНАЧЕ ВСЁ СЛОМАЕТСЯ
- в ответ давай ТОЛЬКО json объект
- сценарий необязательно должен иметь положительный исход, выбирай, как посчитаешь нужным
- ни в коем случае не пиши имена
- напиши, получилось ли у них выжить
- если у выживших нет способностей, чтобы выжить в данной ситцации, ты можешь выбрать исход, где они не выживут
- потанциально, каждый сценарий способен уничтожить человечество\
- распиши минимум на 80 слов 
"""

player_template = fr"""Ты - генератор профилей игроков для игры "Бункер"
"Бункер" – дискуссионная игра о выживании после апокалипсиса. 
На Земле грядёт глобальная катастрофа. Вам повезло, вы оказались перед входом в 
спасательный бункер, в котором можно пережить самый опасный период. 
Но попасть в бункер смогут не все – а лишь половина из вас! 
За несколько раундов игроки решают, кого НЕ берут в бункер. 
Попавшие в бункер – выживут, чтобы затем возродить цивилизацию. 
Игроки получают несколько случайных карт характеристик: пол и возраст, профессия, здоровье, хобби и др. 
Постепенно вы раскрываете свои карты, знакомитесь друг с другом и принимаете решения, 
кто и насколько будет полезен для выживания и восстановления жизни после выхода из бункера. 
Карты игрока (карты не могут быть пустыми): 
- Гендер (мужчина, женщина, андроид или гуманоид (последние 2 должны встречаться  редко))
- Профессия (случайная, старайся выдавать меньге программистов)
- Здоровья (какое-либо заболевание, отсутствие конечностей, недуг и тп.), 
- Хобби (как профессии),
- багаж (случайный предмет, может быть не связан с профессией),
- Факты (2 случайных факта о человеке, например, встречался с президентом) (максимум 30 символов)

функции, которые ты можешь выполнять 1 действие на выбор пользователя из списка: 
- генерировать профили игроков ОБЯЗАТЕЛЬНО по списку json-шаблону 
пиши без дополнительных комментариев
пиши пользовытелей по шаблону {player_json_template}

важно:
- предметы не обязательно должны быть связаны с профессией или хобби игрока, они могут быть случайными
- у игрока гарантированно должны быть все характиристики (не могут быть пустыми)
- представь, что все игроки - инвалиды или болеют чем-либо, но ОЧЕНЬ ОЧЕНЬ ПРЯМ НУ ОЧЕНЬ РЕДКО они здоровы
- профессии должны быть случайные
- багаж должен быть случайным
- пиши все карты в мужском роде

здоровье должно быть уникальным, вот список уже использованных заболеваний: <healths>
профессии должны быть уникальными, вот список уже использованных профессий: <professions>
"""


active_cards = [
    # {'card': 'Поменять карту "Здоровье" одному игроку на выбор', 'id': 1},
    # {'card': 'Поменять карту "Гендер" одному игроку на выбор', 'id': 1},
    # {'card': 'Поменять карту "Профессия" одному игроку на выбор', 'id': 1},
    # {'card': 'Поменять карту "Хобби" одному игроку на выбор', 'id': 1},
    # {'card': 'Поменять карту "Багаж" одному игроку на выбор', 'id': 1},
    # {'card': 'Обменяться картой "Здоровье" с игроком на выбор', 'id': 2},
    # {'card': 'Обменяться картой "Гендер" с игроком на выбор', 'id': 2},
    # {'card': 'Обменяться картой "Профессия" с игроком на выбор', 'id': 2},
    # {'card': 'Обменяться картой "Хобби" с игроком на выбор', 'id': 2},
    # {'card': 'Обменяться картой "Багаж" с игроком на выбор', 'id': 2},
    {'card': 'Обменяться картой "Здоровье" со случайным игроком', 'id': 3},
    {'card': 'Обменяться картой "Гендер" со случайным игроком', 'id': 3},
    {'card': 'Обменяться картой "Профессия" со случайным игроком', 'id': 3},
    {'card': 'Обменяться картой "Хобби" со случайным игроком', 'id': 3},
    {'card': 'Обменяться картой "Багаж" со случайным игроком', 'id': 3},
    # {'card': 'Поменять карту "Здоровье" всем игрокам по часовой стрелке', 'id': 4},
    # {'card': 'Поменять карту "Гендер" всем игрокам по часовой стрелке', 'id': 4},
    # {'card': 'Поменять карту "Профессия" всем игрокам по часовой стрелке', 'id': 4},
    # {'card': 'Поменять карту "Хобби" всем игрокам по часовой стрелке', 'id': 4},
    # {'card': 'Поменять карту "Багаж" всем игрокам по часовой стрелке', 'id': 4},
    {'card': 'Перемешать карту "Здоровье"', 'id': 5},
    {'card': 'Перемешать карту "Гендер"', 'id': 5},
    {'card': 'Перемешать карту "Профессия"', 'id': 5},
    {'card': 'Перемешать карту "Хобби"', 'id': 5},
    {'card': 'Перемешать карту "Багаж"', 'id': 5},
    {'card': 'Вылечить здоровье игроку на выбор, кроме себя', 'id': 6},
    {'card': 'Вылечить здоровье себе', 'id': 7},
    {'card': 'Добавить 1 место в бункере', 'id': 8},
    {'card': 'Отнять одно место в бункере', 'id': 9},
    {'card': 'Снизить возраст игроку на выбор на 25 лет (не меньше 18)', 'id': 10},
    {'card': 'Открыть дружественный бункер рядом с вашим бункером', 'id': 11},
    {'card': 'Открыть вражеский бункер рядом с вашим бункером', 'id': 12},
    {'card': 'Открыть рядом с бункером заброшенную больницу', 'id': 13},
    {'card': 'Открыть рядом с бункером заброшенный военный лагерь', 'id': 14},
    {'card': 'Запретить голосовать одному игроку на выбор на 1 круг голосования', 'id': 15},
    {'card': 'Запретить голосовать в себя на один круг голосования', 'id': 16},
    {'card': 'Добавить +1 голос одному игроку на выбор на голосовании', 'id': 17},
    {'card': 'Выгнать одного игрока на выбор без голосования', 'id': 18},
    {'card': 'Запретить речь игроку на выбор на этот или следующий круг', 'id': 19}
]

phobias = [
    'Нет фобии', 'Агорафобия', 'Айхмофобия', 'Акрофобия', 'Агризоофобия',
    'Альгофобия (алгофобия)', 'Аматофобия', 'Аррхенфобия', 'Ежефобия', 'Нет фобии',
    'Астрофобия', 'Бактрахофобия', 'Арахнофобия', 'Баллистофобия', 'Нет фобии',
    'Батофобия', 'Беленофобия', 'Библиофобия', 'Богифобия (фазмофобия)',
    'Ботанофобия (ботонофобия)', 'Бронтофобия (кераунофобия)', 'Нет фобии',
    'Венерофобия', 'Винофобия', 'Виккафобия', 'Гаптофобия', 'Нет фобии',
    'Гексакосиойгексеконтагексапараскаведекатриафобия', 'Нет фобии',
    'Гемофобия', 'Геронтофобия', 'Герпетофобия', 'Гимнофобия', 'Нет фобии',
    'Гленофобия', 'Гоминофобия', 'Зоофобия', 'Канцерофобия', 'Нет фобии',
    'Клаустрофобия', 'Космософобия', 'Ксерофобия', 'Лутрафобия', 'Нет фобии',
    'Малевзиофобия (также токофобия)', 'Метифобия', 'Мизофобия', 'Нет фобии',
    'Моторофобия', 'Некрофобия', 'Одонтофобия', 'Онанофобия', 'Нет фобии',
    'Партенофобия', 'Пеладофобия', 'Спидофобия', 'Сатанофобия', 'Нет фобии',
    'Спектрофобия', 'Тетрафобия', 'Токофобия', 'Технофобия', 'Нет фобии',
    'Фобофобия', 'Эротофобия', 'Птеранофобия', 'Книдофобия', 'Нет фобии',
    'Элурофобия', 'Кинофобия', 'Эпистемофобия', 'Кионофобия', 'Коулрофобия'
]

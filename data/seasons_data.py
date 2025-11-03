from models import Season
from extensions import db


SEASONS_INFO = {
    1: {
        'registration_start': '2024-05-20',
        'registration_end': '2024-06-01',
        'cost': 0,
        'raketo_ref': 'https://raketo.app/tournamentDetails?tournamentRef=NJqr1JEpBVCcSPKfK9Xc',
        'prize_positions': ['M1a - 1 место', 'M1b - 1 место'],
        'prize_amount': 150000,
        'lottery_minimum_matches': 7,
        'lottery_amount': 150000,
        'lottery_count': 1,
        'relegations': {'M1a, M1b': ['Топ-8 игроков выходят в M1 (сквозная сортировка)']},
        'special_rules': ['После завершения месяца первые места групп играют финал за первое место в сезоне']
    },
    2: {
        'registration_start': '2024-06-25',
        'registration_end': '2024-07-01',
        'cost': 100000,
        'raketo_ref': 'https://raketo.app/tournamentDetails?tournamentRef=o0mtSkzlRKoiiijwzRmo',
        'prize_positions': ['M1 - 1, 2 место', 'M2 - 1, 2 место'],
        'prize_amount': 200000,
        'lottery_minimum_matches': 7,
        'lottery_amount': 200000,
        'lottery_count': 1,
        'relegations': {'M1': ['понижение: bottom-4'], 'M2': ['повышение: top-3', 'понижение: bottom-2 ']},
        'special_rules': ['Нет']
    },
    3: {
        'registration_start': '2024-06-25',
        'registration_end': '2024-07-01',
        'cost': 100000,
        'raketo_ref': 'https://raketo.app.link/oOKLWTaUuLb',
        'prize_positions': ['M1 - 1, 2, 3 место', 'M2 - 1, 2, 3 место'],
        'prize_amount': 200000,
        'lottery_minimum_matches': 7,
        'lottery_amount': 200000,
        'lottery_count': 1,
        'relegations': {'M1': ['понижение: bottom-5'], 'M2': ['повышение: top-3', 'понижение: bottom-2 ']},
        'special_rules': ['Нет']
    },
    4: {
        'registration_start': '2024-09-15',
        'registration_end': '2024-09-23',
        'cost': 100000,
        'raketo_ref': 'https://raketo.app.link/6NgJijC05Mb',
        'prize_positions': ['M1 - 1, 2 место', 'M2 - 1, 2 место', 'M3 - 1, 2 место'],
        'prize_amount': 200000,
        'lottery_minimum_matches': 7,
        'lottery_amount': 200000,
        'lottery_count': 2,
        'relegations': {'M1': ['понижение: bottom-4'], 'M2': ['повышение: top-3', 'понижение: bottom-2'],
                        'M3': ['повышение: top-3']},
        'special_rules': ['Нет']
    },
    5: {
        'registration_start': '2025-02-15',
        'registration_end': '2025-02-22',
        'cost': 130000,
        'raketo_ref': 'https://raketo.app.link/bDoqC0ZueSb',
        'prize_positions': ['Masters - 1, 2, 3 место', 'Open - 1, 2, 3 место'],
        'prize_amount': 300000,
        'lottery_minimum_matches': 7,
        'lottery_amount': 300000,
        'lottery_count': 2,
        'relegations': {},
        'special_rules': ['Одна общая группа для Masters и одна для Open', 'Результаты не влияют на рейтинг',
                          'Учитываются лучшие 7 игр'],
        'description': 'Подготовительный сезон вне зачета - 1 общий дивизион',
    },
    6: {
        'registration_start': '2025-04-01',
        'registration_end': '2025-04-20',
        'cost': 130000,
        'raketo_ref': 'https://raketo.app.link/bDoqC0ZueSb',
        'prize_positions': ['M1 - 1, 2 место', 'M2 - 1, 2 место', 'M3 - 1, 2 место', 'M4 - 1, 2 место'],
        'prize_amount': 300000,
        'lottery_minimum_matches': 7,
        'lottery_amount': 200000,
        'lottery_count': 6,
        'relegations': {'M1': ['понижение: bottom-4'], 'M2': ['повышение: top-3', 'понижение: bottom-3'],
                        'M3': ['повышение в M1: top-1', 'повышение в M2: 2, 3, 4 места', 'понижение: bottom-1'],
                        'M4': ['повышение: top-3'], },
        'special_rules': ['Объединенный дивизион M3: формирование M3-M4 по ходу сезона 27.04.2025',
                          'Топ-5 из двух подгрупп объединяются в дивизион M3, остальные участники двух подгрупп объединяются в дивизион M4',
                          'Игры с игроками, которые попали в ту же подгруппу, если они были сыграны до 27.04 переигрывать нельзя и не нужно - они учитываются как есть. Если такая игра не была сыграна до 27.04 - ее можно сыграть до 18.05',
                          ],
        'special_dates': {'2025-04-27': 'Перегруппировка дивизионов M3-M4'},
        'description': 'Первый рейтинговый сезон года',
    },
    7: {
        'registration_start': '2025-07-01',
        'registration_end': '2025-07-27',
        'cost': 130000,
        'raketo_ref': 'https://raketo.app.link/FKrblQYlHUb',
        'prize_positions': ['M1 - 1, 2, 3 место', 'M2 - 1, 2 место', 'M3 - 1, 2 место'],
        'prize_amount': 300000,
        'lottery_minimum_matches': 7,
        'lottery_amount': 200000,
        'lottery_count': 7,
        'relegations': {'M1': ['понижение: bottom-4'], 'M2': ['повышение: top-3', 'понижение: bottom-3'],
                        'M3': ['повышение: top-3', 'понижение: bottom-3'],
                        'M4': ['повышение: top-3', 'понижение: bottom-2'],
                        'O1': ['повышение: top-3']},
        'special_rules': ['Быстрый переход для лидеров групп 1.08.2025 по желанию',
                          'При переходе в дивизион выше сгорают все набранные очки. Но матчи учитываются для определения приза за активность',
                          'Третье место (непризовое) - может по своему желанию отказаться от перехода в дивизион выше'],
        'special_dates': {'2025-08-01': 'Быстрый переход'},
        'description': 'Летний сезон',
    },
    8: {
        'year': 2025,
        'name': '3',
        'date_start': '2025-09-15',
        'date_end': '2025-11-02',
        'registration_start': '2025-09-08',
        'registration_end': '2025-10-05',
        'cost': 130000,
        'raketo_ref': 'https://raketo.app.link/XdJwhhziuWb',
        'prize_positions': ['M1 - 1, 2, 3 места', 'M2 - 1, 2, 3  места', 'M3 - 1, 2, 3 места',
                            'M4a - 1, 2 места', 'M4b - 1, 2  места', 'O1 - 1, 2 места', ],
        'prize_amount': 300000,
        'lottery_minimum_matches': 7,
        'lottery_amount': 200000,
        'lottery_count': '6',
        'relegations': {'M1': ['понижение: bottom-4'],
                        'M2': ['повышение: top-3', 'понижение: bottom-4'],
                        'M3': ['повышение: top-3', 'понижение: bottom-4'],
                        'M4a/b': ['повышение: top-2', 'понижение: bottom-3'],
                        'O1': ['повышение: top-3']},
        'special_rules': ['Действует правило быстрого перехода (дата - 5.10.2025)',
                          "По итогам сезона формируется +1 дивизион в соостветствии с рейтингом",
                          'Регламент будет уточнен по итогам регистрации в зависимости от заявки'],
        'description': 'Осенний сезон',
        'is_completed': False
    },
    9: {
            'year': 2025,
            'name': '4',
            'date_start': '2025-11-08',
            'date_end': '2025-12-14',
            'registration_start': '2025-11-03',
            'registration_end': '2025-11-09',
            'cost': 130000,
            'raketo_ref': '',
            'prize_positions': [],
            'prize_amount': 300000,
            'lottery_minimum_matches': 7,
            'lottery_amount': 200000,
            'lottery_count': 'уточняется',
            'relegations': {},
            'special_rules': [],
            'description': 'Завершающий сезон года',
            'is_completed': False,
    },
    10: {
            'year': 2025,
            'name': 'Amazing Slam',
            'date_start': '2025-06-01',
            'date_end': '2025-06-28',
            'registration_start': '2025-05-21',
            'registration_end': '2025-06-01',
            'cost': 130000,
            'raketo_ref': '',
            'prize_positions': [],
            'prize_amount': 300000,
            'lottery_minimum_matches': 0,
            'lottery_amount': 200000,
            'lottery_count': 0,
            'relegations': {},
            'special_rules': [],
            'description': 'Большой турнир по олимпийской системе',
            'is_completed': False,
            'is_ranked': False,
    }
}







def init_seasons_data():
    """Инициализировать данные сезонов"""
    new_seasons = []

    for season_id, season_info in SEASONS_INFO.items():
        season = db.session.get(Season, season_id)
        if season:
            season.update_from_info(season_info)
        else:
            season = Season(league_id=1)
            season.update_from_info(season_info)
            new_seasons.append(season)

    db.session.add_all(new_seasons)

    db.session.commit()
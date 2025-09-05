from flask import render_template, redirect, url_for
from init import create_app
from models import Player, League, Season, Division, Result, Ranking, get_last_result_before_date
from extensions import db
import json
from datetime import datetime
import os


app = create_app()


def delete_all():
    Ranking.query.delete()
    Result.query.delete()
    Player.query.delete()
    Division.query.delete()
    Season.query.delete()
    League.query.delete()

    db.session.commit()
    return



def input_data_from_json(file):
    """Add all leagues, seasons, divisions, players, results from file.

    Must be invoked within app_context.
    """
    d = json.load(file)

    for name in d:
        league = League(name=name)
        db.session.add(league)
        db.session.commit()

        for s in d[name]:
            season = Season(name=s['name'], year=s['year'], league_id=league.id,
                            date_start=datetime.strptime(s['date_start'], "%Y-%m-%d"),
                            date_end=datetime.strptime(s['date_end'], "%Y-%m-%d"))
            db.session.add(season)
            db.session.commit()

            for d in s['divisions']:
                division = Division(name=d['name'], priority=d['priority'], season_id=season.id)
                db.session.add(division)
                db.session.commit()

                for r in d['results']:
                    player = Player.query.filter_by(first_name=r['first_name'],
                                                    last_name=r['last_name']).first()
                    if player is None:
                        player = Player(first_name=r['first_name'],
                                        last_name=r['last_name'],
                                        gender=r['gender'])
                        db.session.add(player)
                        db.session.commit()

                    result = Result(player_id=player.id,
                                    position=r['position'],
                                    match_count=r['match_count'],
                                    win_count=r['win_count'],
                                    tie_win_count=r['tie_win_count'],
                                    set_diff=r['set_diff'],
                                    game_diff=r['game_diff'],
                                    division_id=division.id,
                                    relegation=r['relegation']
                                    )
                    db.session.add(result)
                    db.session.commit()


def calculate_rankings(date):
    """
    Calculate rankings for given date
    """
    results = []

    for player in Player.query.all():
        last_result = get_last_result_before_date(player.id, date)
        if last_result:
            relegation = last_result.relegation
            prev_priority = last_result.division_ref.priority
            position = last_result.position
            result_date = last_result.division_ref.season_ref.date_end

            if relegation == 'promoted' or relegation == 'fast promoted':
                new_priority = prev_priority - 10
            elif relegation ==  'relegated':
                new_priority = prev_priority + 10
            elif relegation == 'double promoted':
                new_priority = prev_priority - 20
            else:
                new_priority = prev_priority

            results.append({'last_result': last_result,
                            'new_priority': new_priority,
                            'prev_priority': prev_priority,
                            'position': position,
                            'result_date': result_date,
                            'player': player})


    sorted_items = sorted(
        results,
        key=lambda x: (
            x['new_priority'], # (ascending)
            x['prev_priority'],  # (ascending)
            x['position'],  # (ascending)
            -(x['result_date'].toordinal())  # (descending)
        )
    )

    rankings = []
    for i, value in enumerate(sorted_items):
        ranking = Ranking(player_id=value['player'].id,
                          position=i+1,
                          actual_date=value['result_date'],
                          actual_season_id=value['last_result'].division_ref.season_id,
                          last_result_id=value['last_result'].id)

        rankings.append(ranking)

        db.session.add(ranking)

    db.session.commit()

    return rankings








@app.route('/')
def index():
    return render_template('index.html')


@app.route('/results')
def show_ratings():
    results = Result.query.all()
    results_data = [p.to_dict() for p in results]

    seasons = Season.query.all()
    seasons_data = [s.to_dict() for s in seasons]

    return render_template('results.html', results=results_data, all_seasons=seasons_data)


@app.route('/rankings')
def show_rankings():
    last_date = Season.query.order_by(Season.date_end.desc()).first().date_end
    rankings = Ranking.query.filter_by(actual_date=last_date).order_by('position').all()
    rankings_data = [p.to_dict() for p in rankings]

    return render_template('rankings.html', rankings=rankings_data)


@app.route('/results/<season_id>')
def show_rating_for_season(season_id):
    results = Result.query.join(Result.division_ref).filter(Division.season_id == season_id).all()
    results_data = [p.to_dict() for p in results]

    all_seasons = Season.query.all()
    seasons_data = [s.to_dict() for s in all_seasons]

    selected_season = Season.query.get(season_id)

    if not selected_season:
        return redirect(url_for('show_ratings'))

    selected_season = selected_season.to_dict()

    return render_template('results.html', results=results_data,
                           all_seasons=seasons_data, selected_season=selected_season)


@app.route('/regulations')
def show_regulations():
    return render_template('regulations.html')


@app.template_filter('to_date')
def to_date_filter(date_string):
    try:
        return datetime.strptime(date_string, '%Y-%m-%d').date()
    except:
        return None

@app.route('/faq')
def faq():
    return render_template('faq.html')


@app.route('/schedule')
def show_schedule():
    # Season data - you can also move this to a database later
    seasons = [
        {
            'name': 'Preseason',
            'start_date': '2025-02-22',
            'end_date': '2025-03-30',
            'status': 'upcoming',
            'description': 'Подготовительный сезон вне зачета - 1 общий дивизион',
            'rating': 'Вне зачета',
        },
        {
            'name': 'Season 1',
            'start_date': '2025-04-05',
            'end_date': '2025-05-18',
            'status': 'upcoming',
            'description': 'Первый рейтинговый сезон года',
            'rating': 'Рейтинговый',
        },
        {
            'name': 'Masters Slam',
            'start_date': '2025-06-01',
            'end_date': '2025-06-28',
            'status': 'upcoming',
            'description': 'Турнир на вылет для всех участников лиги',
            'rating': 'Вне зачета',
        },
        {
            'name': 'Season 2',
            'start_date': '2025-07-06',
            'end_date': '2025-08-31',
            'status': 'upcoming',
            'description': 'Летний сезон',
            'rating': 'Рейтинговый',
        },
        {
            'name': 'Season 3',
            'start_date': '2025-09-15',
            'end_date': '2025-11-02',
            'status': 'upcoming',
            'description': 'Осенний сезон',
            'rating': 'Рейтинговый',
        },
        {
            'name': 'Season 4',
            'start_date': '2025-11-10',
            'end_date': '2025-12-14',
            'status': 'upcoming',
            'description': 'Завершающий сезон года',
            'rating': 'Рейтинговый',
        }
    ]

    # Calculate current season status
    current_date = datetime.now().date()
    for season in seasons:
        start = datetime.strptime(season['start_date'], '%Y-%m-%d').date()
        end = datetime.strptime(season['end_date'], '%Y-%m-%d').date()

        if start <= current_date <= end:
            season['status'] = 'current'
        elif current_date > end:
            season['status'] = 'completed'
        elif current_date < start:
            season['status'] = 'upcoming'

    return render_template('schedule.html', seasons=seasons, current_year=2025)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()

        delete_all()

        if Player.query.count() == 0:
            with open('misc/results_season12025_1.json') as f:
                input_data_from_json(f)

        if Ranking.query.count() == 0:
            seasons = Season.query.order_by('date_end').all()
            for s in seasons:
                if s.name == 'Preseason':
                    pass
                calculate_rankings(s.date_end)

    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

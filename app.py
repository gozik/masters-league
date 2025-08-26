from flask import render_template, redirect, url_for
from init import create_app
from models import Player, League, Season, Division, Result
from extensions import db
import json
from datetime import datetime




app = create_app()


def input_data_from_json(file):
    """Initialize database with sample data"""
    with app.app_context():
        # Only create sample data if database is empty
        if Player.query.count() == 0:
            d = json.load(file)

            # Create sample season
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

    return render_template('results.html', results=results_data, all_seasons=seasons_data, selected_season=selected_season)


@app.route('/regulations')
def show_regulations():
    return render_template('regulations.html')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        with open('misc/results_season12025_1.json') as f:
            input_data_from_json(f)
    app.run(debug=True, port=int(os.environ.get('PORT', 8080)))

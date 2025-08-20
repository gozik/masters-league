from flask import render_template
from init import create_app
from models import Player, League, Season, Division, Result
from extensions import db


app = create_app()


def create_sample_data(force_add=False):
    """Initialize database with sample data"""
    with app.app_context():
        db.create_all()

        # Only create sample data if database is empty
        if force_add or Player.query.count() == 0:
            # Create sample league
            league = League(name='Tashkent Masters')
            db.session.add(league)
            db.session.commit()

            # Create sample season
            season = Season(name='1', year=2025, league_id=league.id)
            db.session.add(season)
            db.session.commit()

            # Create sample division
            division = Division(name='M1', priority=10, season_id=season.id)
            db.session.add(division)
            db.session.commit()

            # Create sample players
            players_data = [
                {'first_name': 'Rogozin', 'last_name': 'Anton', 'gender': 'male'},
                {'first_name': 'Razzakov', 'last_name': 'Alisher', 'gender': 'male'},
                {'first_name': 'Larionov', 'last_name': 'Svyatoslav', 'gender': 'male'},
                {'first_name': 'Shirinov', 'last_name': 'Jahon', 'gender': 'male'},
                {'first_name': 'Shamuratov', 'last_name': 'Farrukh', 'gender': 'male'},
                {'first_name': 'Musadjanov', 'last_name': 'Hatam', 'gender': 'male'},
                {'first_name': 'Malikov', 'last_name': 'Humoyun', 'gender': 'male'},
                {'first_name': 'Kamilov', 'last_name': 'Baxriddin', 'gender': 'male'},
                {'first_name': 'Vohidov', 'last_name': 'Nodir', 'gender': 'male'},
            ]

            players = []
            for data in players_data:
                player = Player(first_name=data['first_name'], last_name=data['last_name'],
                                gender=data['gender'])
                db.session.add(player)
                players.append(player)

            db.session.commit()

            result_data = [(8, 7, 0, 11, 46),
                           (6, 6, 0, 12, 37),
                           (6, 4, 0, 5, 18),
                           (5, 4, 0, 3, -1),
                           (7, 3, 1, -2, -17),
                           (8, 3, 0, -4, 3),
                           (6, 2, 0, -3, -11),
                           (6, 0, 0, -11, -33),
                           (6, 0, 0, -11, -42)]

            results = []
            for i in range(0, len(players)):
                result = Result(player_id=players[i].id,
                                position=i+1,
                                match_count=result_data[i][0],
                                win_count=result_data[i][1],
                                tie_win_count=result_data[i][2],
                                set_diff=result_data[i][3],
                                game_diff=result_data[i][4],
                                division_id=division.id,
                                relegation=('relegated' if i>4 else 'unchanged'),
                                )
                db.session.add(result)
                results.append(result)

            db.session.commit()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/results')
def show_ratings():
    results = Result.query.all()
    results_data = [p.to_dict() for p in results]

    return render_template('results.html', results=results_data)


if __name__ == '__main__':
    with app.app_context():
        create_sample_data()
    app.run(debug=True)

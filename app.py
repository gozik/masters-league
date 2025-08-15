from flask import render_template
from init import create_app
from models import Player, Rating, Match
from extensions import db
from datetime import datetime
import random


app = create_app()


def create_sample_data():
    """Initialize database with sample data"""
    with app.app_context():
        db.create_all()

        # Only create sample data if database is empty
        if Player.query.count() == 0:
            # Create sample players
            players_data = [
                {'first_name': 'Novak', 'last_name': 'Djokovic', 'country': 'SRB', 'birth_date': datetime(1987, 5, 22),
                 'gender': 'M', 'current_rating': 9850},
                {'first_name': 'Daniil', 'last_name': 'Medvedev', 'country': 'RUS', 'birth_date': datetime(1996, 2, 11),
                 'gender': 'M', 'current_rating': 8930},
                {'first_name': 'Rafael', 'last_name': 'Nadal', 'country': 'ESP', 'birth_date': datetime(1986, 6, 3),
                 'gender': 'M', 'current_rating': 8425},
                {'first_name': 'Stefanos', 'last_name': 'Tsitsipas', 'country': 'GRE',
                 'birth_date': datetime(1998, 8, 12), 'gender': 'M', 'current_rating': 7980},
                {'first_name': 'Alexander', 'last_name': 'Zverev', 'country': 'GER',
                 'birth_date': datetime(1997, 4, 20), 'gender': 'M', 'current_rating': 7865},
                {'first_name': 'Iga', 'last_name': 'Świątek', 'country': 'POL', 'birth_date': datetime(2001, 5, 31),
                 'gender': 'F', 'current_rating': 9230},
                {'first_name': 'Aryna', 'last_name': 'Sabalenka', 'country': 'BLR', 'birth_date': datetime(1998, 5, 5),
                 'gender': 'F', 'current_rating': 8765},
            ]

            players = []
            for data in players_data:
                player = Player(**data)
                db.session.add(player)
                players.append(player)

            db.session.commit()

            # Create sample ratings
            for player in players:
                for i in range(5):
                    rating = Rating(
                        player_id=player.id,
                        rating=player.current_rating - random.randint(0, 200),
                        date=datetime(2023, 12 - i, 1),
                        tournament=f"Sample Tournament {i + 1}"
                    )
                    db.session.add(rating)

            # Create sample matches
            for i in range(10):
                player1 = random.choice(players)
                player2 = random.choice([p for p in players if p.id != player1.id])

                match = Match(
                    player1_id=player1.id,
                    player2_id=player2.id,
                    winner_id=random.choice([player1.id, player2.id]),
                    score=f"{random.randint(0, 6)}-{random.randint(0, 6)} {random.randint(0, 6)}-{random.randint(0, 6)}",
                    date=datetime(2023, random.randint(1, 12), random.randint(1, 28)),
                    tournament=f"Sample Tournament {random.randint(1, 5)}",
                    round=random.choice(["1st Round", "2nd Round", "QF", "SF", "F"])
                )
                db.session.add(match)

            db.session.commit()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/ratings')
def show_ratings():
    players = Player.query.order_by(Player.current_rating.desc()).all()
    players_data = [p.to_dict() for p in players]

    return render_template('ratings.html', players=players_data)


if __name__ == '__main__':
    with app.app_context():
        create_sample_data()
    app.run(debug=True)
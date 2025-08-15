from extensions import db
from datetime import datetime

class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    country = db.Column(db.String(3), nullable=False)
    birth_date = db.Column(db.Date)
    gender = db.Column(db.String(1))  # 'M' or 'F'
    current_rating = db.Column(db.Float)
    ratings = db.relationship('Rating', backref='player', lazy=True)
    matches = db.relationship('Match', foreign_keys='Match.player1_id', backref='player1', lazy=True)
    matches2 = db.relationship('Match', foreign_keys='Match.player2_id', backref='player2', lazy=True)


    def to_dict(self):
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'country': self.country,
            'birth_date': self.birth_date.isoformat() if self.birth_date else None,
            'current_rating': self.current_rating,
            'age': self.age
        }


    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


    @property
    def age(self):
        if self.birth_date:
            today = datetime.today()
            return today.year - self.birth_date.year - (
                        (today.month, today.day) < (self.birth_date.month, self.birth_date.day))
        return None


class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)
    rating = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, default=datetime.utcnow)
    tournament = db.Column(db.String(100))


class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player1_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)
    player2_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)
    winner_id = db.Column(db.Integer, db.ForeignKey('player.id'))
    score = db.Column(db.String(50))
    date = db.Column(db.Date, nullable=False)
    tournament = db.Column(db.String(100))
    round = db.Column(db.String(50))

    player_winner = db.relationship('Player', foreign_keys=[winner_id])
from sqlalchemy import Enum
from extensions import db


class Player(db.Model):
    """Represents a tennis player in the league"""
    __tablename__ = 'Player'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    first_name = db.Column(db.String(64), nullable=True)
    last_name = db.Column(db.String(64), nullable=True)
    gender = db.Column(Enum('male', 'female', name='gender_enum'), nullable=True)

    results = db.relationship('Result', backref='player_ref', lazy=True)

    __table_args__ = (db.Index('idx_player_name', 'last_name', 'first_name'),)

    def to_dict(self):
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
        }

    def __repr__(self):
        return f'<Player {self.first_name} {self.last_name}>'




class League(db.Model):
    """Represents a tennis league"""
    __tablename__ = 'League'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(64), nullable=False)

    seasons = db.relationship('Season', backref='league_ref', lazy=True)

    def __repr__(self):
        return f'<{self.name} League>'


class Season(db.Model):
    """Represents a season within a league"""
    __tablename__ = 'Season'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(64), nullable=True)
    year = db.Column(db.Integer, nullable=True)
    date_start = db.Column(db.Date, nullable=True)
    date_end = db.Column(db.Date, nullable=True)
    league_id = db.Column(db.Integer, db.ForeignKey('League.id'), nullable=False)

    divisions = db.relationship('Division', backref='season_ref', lazy=True)


    def __repr__(self):
        return f'<Season {self.name} ({self.year})>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'year': self.year,
            'date_start': self.date_start,
            'date_end': self.date_end,
        }

    def get_title(self):
        return f'{self.year}/{self.name}'


class Division(db.Model):
    """Represents a group/division within a season"""
    __tablename__ = 'Division'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(64), nullable=True)
    priority = db.Column(db.Integer, nullable=True)
    season_id = db.Column(db.Integer, db.ForeignKey('Season.id'), nullable=False)

    results = db.relationship('Result', backref='division_ref', lazy=True)

    def __repr__(self):
        return f'<Division {self.name}>'


class Result(db.Model):
    """Represents a player's results in a specific division"""
    __tablename__ = 'Result'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    player_id = db.Column(db.Integer, db.ForeignKey('Player.id'), nullable=True)
    position = db.Column(db.Integer, nullable=True)
    match_count = db.Column(db.Integer, nullable=True)
    win_count = db.Column(db.Integer, nullable=True)
    tie_win_count = db.Column(db.Integer, nullable=True)
    set_diff = db.Column(db.Integer, nullable=True)
    game_diff = db.Column(db.Integer, nullable=True)
    division_id = db.Column(db.Integer, db.ForeignKey('Division.id'), nullable=True)
    relegation = db.Column(Enum('promoted', 'relegated', 'unchanged', 'fast promoted', 'double promoted',
                                name='relegation_enum'), nullable=True)

    def __repr__(self):
        return f'<Result Player {self.player_id} in Division {self.division_id}>'


    def to_dict(self):
        return {
            'id': self.id,
            'first_name': self.player_ref.first_name,
            'last_name': self.player_ref.last_name,
            'position': self.position,
            'match_count': self.match_count,
            'win_count': self.win_count,
            'relegation': self.relegation,
            'season': self.division_ref.season_ref.get_title(),
            'division': self.division_ref.name
        }

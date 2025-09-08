from datetime import datetime, timedelta
from sqlalchemy import Enum, CheckConstraint
from extensions import db



class Player(db.Model):
    """Represents a tennis player in the league"""
    __tablename__ = 'Player'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    first_name = db.Column(db.String(64), nullable=True)
    last_name = db.Column(db.String(64), nullable=True)
    gender = db.Column(Enum('male', 'female', name='gender_enum'), nullable=True)

    results = db.relationship('Result', backref='player_ref', lazy=True)
    rankings = db.relationship('Ranking', backref='player_ref', lazy=True)

    __table_args__ = (db.Index('idx_player_name', 'last_name', 'first_name'),)

    def to_dict(self):
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
        }

    def __repr__(self):
        return f'<{self.first_name} {self.last_name}>'



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
    is_ranked = db.Column(db.Boolean, default=True)
    is_completed = db.Column(db.Boolean, default=True)
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

    ranking = db.relationship('Ranking', backref='last_result_ref', lazy=True)

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
            'division': self.division_ref.name,
            'player_id': self.player_id,
        }


class Ranking(db.Model):
    """Represents a player's position in the league"""
    __tablename__ = 'Ranking'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    player_id = db.Column(db.Integer, db.ForeignKey('Player.id'), nullable=True)
    position = db.Column(db.Integer, nullable=False)
    career_high = db.Column(db.Integer, nullable=True)

    actual_date = db.Column(db.Date, nullable=False)
    actual_season_id = db.Column(db.Integer, db.ForeignKey('Season.id'), nullable=False)

    last_result_id = db.Column(db.Integer, db.ForeignKey('Result.id'), nullable=False)

    def __repr__(self):
        return f'<{self.position}: {self.player_ref}>'

    def to_dict(self):
        return {
            'id': self.id,
            'first_name': self.player_ref.first_name,
            'last_name': self.player_ref.last_name,
            'position': self.position,
            'actual_date': self.actual_date,
            'last_relegation': self.last_result_ref.relegation,
            'last_division': self.last_result_ref.division_ref.name,
            'last_position': self.last_result_ref.position,
            'last_result_date': self.last_result_ref.division_ref.season_ref.date_end,
            'player_id': self.player_id,
        }





class Match(db.Model):
    """Represents result of a tennis match between two players"""
    __tablename__ = 'match'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    date_played = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    season_id = db.Column(db.Integer, db.ForeignKey('Season.id'), nullable=False)
    division_id = db.Column(db.Integer, db.ForeignKey('Division.id'), nullable=True)
    player1_id = db.Column(db.Integer, db.ForeignKey('Player.id'), nullable=False)
    player2_id = db.Column(db.Integer, db.ForeignKey('Player.id'), nullable=False)
    winner_id = db.Column(db.Integer, db.ForeignKey('Player.id'), nullable=False)

    is_retired = db.Column(db.Boolean, default=False)

    # Game in sets
    set1_player1 = db.Column(db.Integer, nullable=True)
    set1_player2 = db.Column(db.Integer, nullable=True)
    set2_player1 = db.Column(db.Integer, nullable=True)
    set2_player2 = db.Column(db.Integer, nullable=True)
    set3_player1 = db.Column(db.Integer, nullable=True)
    set3_player2 = db.Column(db.Integer, nullable=True)

    # Tiebreak scores
    tb1_player1 = db.Column(db.Integer, nullable=True)
    tb1_player2 = db.Column(db.Integer, nullable=True)
    tb2_player1 = db.Column(db.Integer, nullable=True)
    tb2_player2 = db.Column(db.Integer, nullable=True)
    tb3_player1 = db.Column(db.Integer, nullable=True)
    tb3_player2 = db.Column(db.Integer, nullable=True)

    # Royal tiebreak (played instead of 3rd set)
    royal_tiebreak_player1 = db.Column(db.Integer, nullable=True)
    royal_tiebreak_player2 = db.Column(db.Integer, nullable=True)

    # Relationships
    season = db.relationship('Season', backref='matches')
    division = db.relationship('Division', backref='matches')
    player1 = db.relationship('Player', foreign_keys=[player1_id], backref='matches_as_player1')
    player2 = db.relationship('Player', foreign_keys=[player2_id], backref='matches_as_player2')
    winner = db.relationship('Player', foreign_keys=[winner_id], backref='matches_won')

    # Add a constraint to ensure a player doesn't play against themselves
    __table_args__ = (
        CheckConstraint('player1_id != player2_id', name='check_different_players'),
    )

    def __repr__(self):
        return f'<Match {self.player1_id} vs {self.player2_id} on {self.date_played}>'

    @property
    def score_summary(self):
        scores = []

        # Set 1
        if self.set1_player1 is not None and self.set1_player2 is not None:
            set1_score = f"{self.set1_player1}-{self.set1_player2}"
            if self.tb1_player1 and self.tb1_player2:
                set1_score += f" ({min(self.tb1_player1, self.tb1_player2)})"
            scores.append(set1_score)

        # Set 2
        if self.set2_player1 is not None and self.set2_player2 is not None:
            set2_score = f"{self.set2_player1}-{self.set2_player2}"
            if self.tb2_player1 and self.tb2_player2:
                set2_score += f" ({min(self.tb2_player1, self.tb2_player2)})"
            scores.append(set2_score)

        # Set 3
        if self.set3_player1 is not None and self.set3_player2 is not None:
            set3_score = f"{self.set3_player1}-{self.set3_player2}"
            if self.tb3_player1 and self.tb3_player2:
                set3_score += f" ({min(self.tb3_player1, self.tb3_player2)})"
            scores.append(set3_score)

        # Royal Tiebreak
        if self.royal_tiebreak_player1 is not None and self.royal_tiebreak_player2 is not None:
            scores.append(f" [{self.royal_tiebreak_player1}-{self.royal_tiebreak_player2}]")

        return " ".join(scores)


def get_last_result_before_date(player_id, target_date, filter_seasons, expire_days):
    """Get the latest result for a player before a specific date using season dates"""
    r = Result.query\
        .join(Division, Result.division_id == Division.id)\
        .join(Season, Division.season_id == Season.id)\
        .filter(
            Result.player_id == player_id,
            Season.date_end <= target_date)  # Season ends before target date

    if filter_seasons == 'ranked':
        r = r.filter(Season.is_ranked == True)

    if expire_days:
        cutoff_date = target_date - timedelta(days=expire_days)
        r = r.filter(Season.date_end >= cutoff_date)

    return r.order_by(Season.date_end.desc(), Division.priority).first()

from datetime import datetime, timedelta
from sqlalchemy import Enum, CheckConstraint
from extensions import db


def get_division_name(priority):
    if priority <= 110:
        return 'M1'
    elif priority <= 120:
        return 'M2'
    elif priority <= 130:
        return 'M3'
    elif priority <= 140:
        return 'M4'
    elif priority <= 150:
        return 'M5'
    elif priority <= 210:
        return 'O1'
    return 'O2'


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

    @property
    def current_ranking(self):
        return get_current_ranking(self.id)


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
    is_completed = db.Column(db.Boolean, default=True)
    is_ranked = db.Column(db.Boolean, default=True)
    date_start = db.Column(db.Date, nullable=True)
    date_end = db.Column(db.Date, nullable=True)
    league_id = db.Column(db.Integer, db.ForeignKey('League.id'), nullable=False)

    registration_start = db.Column(db.Date, nullable=True)
    registration_end = db.Column(db.Date, nullable=True)
    cost = db.Column(db.Integer, default=0)  # Стоимость в сумах
    raketo_ref = db.Column(db.String(500), nullable=True)
    prize_amount = db.Column(db.Integer, default=0)
    lottery_minimum_matches = db.Column(db.Integer, default=7)
    lottery_amount = db.Column(db.Integer, default=0)
    lottery_count = db.Column(db.Integer, default=0)

    description = db.Column(db.String(500), nullable=True)

    # JSON поля для сложных структур
    prize_positions = db.Column(db.JSON, default=list)  # Список призовых мест
    relegations = db.Column(db.JSON, default=dict)  # Правила переходов
    special_rules = db.Column(db.JSON, default=list)  # Особые правила
    special_dates = db.Column(db.JSON, default=dict)  # Особые даты

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
            'registration_start': self.registration_start,
            'registration_end': self.registration_end,
            'cost': self.cost,
            'raketo_ref': self.raketo_ref,
            'prize_amount': self.prize_amount,
            'prize_positions': self.prize_positions or [],
            'lottery_minimum_matches': self.lottery_minimum_matches,
            'lottery_amount': self.lottery_amount,
            'lottery_count': self.lottery_count,
            'relegations': self.relegations or {},
            'special_rules': self.special_rules or [],
            'special_dates': self.special_dates or {},
            'is_ranked': self.is_ranked,
            'is_completed': self.is_completed,
            'description': self.description,
            'status': self.status,
            'registration_status': self.registration_status,
            'completion_rate': self.completion_rate
        }

    def get_title(self):
        return f'{self.year}/{self.name}'

    @property
    def status(self):
        return self.get_status()

    @property
    def registration_status(self):
        return self.get_registration_status()

    @property
    def completion_rate(self):
        return self.get_completion_rate()



    def get_status(self):
        if not self.date_end or not self.date_start:
            return 'undefined'

        current_date = datetime.now().date()

        if self.date_end < current_date:
            return 'completed'
        elif self.date_start <= current_date <= self.date_end:
            return 'current'
        else:
            return 'upcoming'


    def get_registration_status(self):
        if not self.registration_start or not self.registration_end:
            return 'closed'

        current_date = datetime.now().date()
        if self.registration_start <= current_date <= self.registration_end:
            return 'open'
        else:
            return 'closed'


    def get_completion_rate(self):
        if not self.date_end or not self.date_start:
            return 0

        current_date = datetime.now().date()
        return max(0., min(1., (current_date - self.date_start).days / (self.date_end - self.date_start).days))


    def update_from_info(self, season_info):
        """Обновить сезон из season_info"""
        simple_fields = [
            'name', 'year',
            'registration_start', 'registration_end', 'cost', 'raketo_ref',
            'prize_amount', 'lottery_minimum_matches', 'lottery_amount', 'lottery_count',
            'description',  'is_ranked', 'is_completed'
        ]
        for field in simple_fields:
            if field in season_info:
                setattr(self, field, season_info[field])

        date_fields = ['registration_start', 'registration_end', 'date_start', 'date_end']
        for field in date_fields:
            if field in season_info:
                setattr(self, field, datetime.strptime(season_info[field], '%Y-%m-%d').date())


        # JSON fields
        json_fields = ['prize_positions', 'relegations', 'special_rules', 'special_dates']
        for field in json_fields:
            if field in season_info:
                setattr(self, field, season_info[field])


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

    def calc_new_priority(self):
        relegation = self.relegation
        prev_priority = self.division_ref.priority

        if relegation == 'promoted' or relegation == 'fast promoted':
            new_priority = prev_priority - 10
            if new_priority == 200:
                new_priority = 150
        elif relegation == 'relegated':
            new_priority = prev_priority + 10
        elif relegation == 'double promoted':
            new_priority = prev_priority - 20
        else:
            new_priority = prev_priority

        return new_priority

    def get_new_division(self):
        return get_division_name(self.calc_new_priority())

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
        relegation_arrow = ''
        if self.last_result_ref.relegation == 'promoted':
            relegation_arrow = '\u21e7'  # arrow up
        elif self.last_result_ref.relegation == 'relegated':
            relegation_arrow = '\u21e9'  # arrow down
        elif self.last_result_ref.relegation == 'double promoted':
            relegation_arrow = '\u21C8'  # double arrow up
        else:
            relegation_arrow = '\u21CF'  # striped arrow

        return {
            'id': self.id,
            'first_name': self.player_ref.first_name,
            'last_name': self.player_ref.last_name,
            'position': self.position,
            'actual_date': self.actual_date,
            'last_result_string': f'{self.last_result_ref.division_ref.name}: {self.last_result_ref.position} {relegation_arrow}',
            'last_season_id': self.actual_season_id,
            'last_relegation': self.last_result_ref.relegation,
            'last_relegation_arrow': relegation_arrow,
            'last_division': self.last_result_ref.division_ref.name,
            'last_position': self.last_result_ref.position,
            'last_result_date': self.last_result_ref.division_ref.season_ref.date_end,
            'player_id': self.player_id,
            'new_priority': self.last_result_ref.calc_new_priority(),
            'new_division': self.last_result_ref.get_new_division(),
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


def get_last_result_before_date(player_id, target_date, filter_seasons, expire_days=None):
    """Get the latest result for a player before a specific date using season dates"""
    r = Result.query \
        .join(Division, Result.division_id == Division.id) \
        .join(Season, Division.season_id == Season.id) \
        .filter(
        Result.player_id == player_id,
        Season.date_end <= target_date)  # Season ends before target date

    if filter_seasons == 'ranked':
        r = r.filter(Season.is_ranked == True)

    if expire_days:
        cutoff_date = target_date - timedelta(days=expire_days)
        r = r.filter(Season.date_end >= cutoff_date)

    return r.order_by(Season.date_end.desc(), Division.priority).first()


def get_current_ranking(player_id):
    """Get player's current ranking"""
    latest_season = Season.query.filter(Season.is_completed == True, Season.is_ranked == True) \
        .order_by(Season.date_end.desc()).first()

    if not latest_season:
        return

    actual_date = latest_season.date_end

    ranking = Ranking.query.filter_by(actual_date=actual_date).filter_by(player_id=player_id).order_by('position').first()

    if ranking:
        return ranking.position
    return None
    # wrong logic for players, without actual result
    # should be ACTUAL RANKING -> get_result(player_id)


def get_results(player_id):
    """Get all season results for the player"""
    return Result.query.filter_by(player_id=player_id).join(Division).join(Season) \
        .order_by(Season.date_end.desc()).all()


def calculate_total_stats(player_id):
    """Calculate total wins, games, and other statistics"""
    results = Result.query.filter_by(player_id=player_id).all()
    rankings = Ranking.query.filter_by(player_id=player_id).all()

    total_wins = sum(result.win_count for result in results)
    total_matches = sum(result.match_count for result in results)
    total_seasons = len(set(result.division_ref.season_id for result in results if result.division_ref))
    if rankings:
        career_high = min(ranking.position for ranking in rankings)
    else:
        career_high = None

    return {
        'total_wins': total_wins,
        'total_matches': total_matches,
        'win_percentage': (total_wins / total_matches * 100) if total_matches > 0 else 0,
        'total_seasons': total_seasons,
        'career_high': career_high
    }

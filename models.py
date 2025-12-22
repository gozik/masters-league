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
                set1_score += f"({min(self.tb1_player1, self.tb1_player2)})"
            scores.append(set1_score)

        # Set 2
        if self.set2_player1 is not None and self.set2_player2 is not None:
            set2_score = f"{self.set2_player1}-{self.set2_player2}"
            if self.tb2_player1 and self.tb2_player2:
                set2_score += f"({min(self.tb2_player1, self.tb2_player2)})"
            scores.append(set2_score)

        # Set 3
        if self.set3_player1 is not None and self.set3_player2 is not None:
            set3_score = f"{self.set3_player1}-{self.set3_player2}"
            if self.tb3_player1 and self.tb3_player2:
                set3_score += f"({min(self.tb3_player1, self.tb3_player2)})"
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


def parse_score(score_string):
    """
    Parse tennis score string into structured format
    Supports formats: "6-3 6-3", "3-6 6-4 [10/8]", "4-6 6-3 [10/4]"
    """
    if not score_string:
        return None

    # Remove any extra spaces and split by space
    parts = score_string.strip().split()

    sets = []
    royal_tiebreak = False
    royal_tiebreak_score = None

    for i, part in enumerate(parts):
        if part.startswith('[') and part.endswith(']'):
            # This is a tiebreak or royal tiebreak
            tiebreak_content = part[1:-1]
            if '/' in tiebreak_content:
                # Format: [10/8] or [10/4]
                royal_tiebreak = True
                royal_score_parts = tiebreak_content.split('/')
                royal_tiebreak_score = (int(royal_score_parts[0]), int(royal_score_parts[1]))

        elif part.startswith('(') and part.endswith(')'):
            # This is a regular tiebreak , must be after regular set
            tiebreak_content = part[1:-1]
            score_parts = tiebreak_content.split('/')
            # The previous set should be a tiebreak
            if sets:
                sets[-1]['tiebreak'] = True
                sets[-1]['tiebreak_score'] = {
                    'player1': int(score_parts[0]),
                    'player2': int(score_parts[1])
                }


        elif '-' in part:
            # Regular set score
            set_parts = part.split('-')
            if len(set_parts) == 2 and set_parts[0].isdigit() and set_parts[1].isdigit():
                sets.append({
                    'player1': int(set_parts[0]),  # Winner's games
                    'player2': int(set_parts[1]),  # Loser's games
                    'tiebreak': False
                })

    return {
        'sets': sets,
        'royal_tiebreak': royal_tiebreak,
        'royal_tiebreak_score': royal_tiebreak_score
    }


def get_season_by_raketo_name(season_name):
    raketo_names = {'Amazing Masters Slam': 10,
                  'Amazing Masters Slam 2': 10,
                  'Amazing Masters Slam 3': 10,
                  'Amazing Open Slam': 10,
                  'Masters League Preseason 2025': 5,
                  'Masters League Season 1/2025': 6,
                  'Masters League Season 2/2025': 7,
                  'Masters League Season 3/2025': 8,
                  'Masters League Season 4/2025': 9,
                  'Open League Preseason 2025': 5,
                  'Open League Season 1/2025': 6,
                  'Tashkent Masters League': 1,
                  'Tashkent Masters League. Season 2': 2,
                  'Tashkent Masters League. Season 3': 3,
                  'Tashkent Masters League. Season 4': 4,
                  'Tashkent Open League': 3,
                  'Tashkent Open League. Season 2': 4, }
    if season_name in raketo_names:
        return Season.query.get(raketo_names[season_name])


def get_common_divisions_in_season(player1_id, player2_id, season_id):
    """
    Find all divisions in a season where both players participated.

    Args:
        player1_id (int): ID of first player
        player2_id (int): ID of second player
        season_id (int): ID of the season

    Returns:
        List of Division objects where both players had results
    """
    # Get divisions where player1 played in the season
    player1_divisions = Division.query \
        .join(Result, Division.id == Result.division_id) \
        .filter(
        Result.player_id == player1_id,
        Division.season_id == season_id
    ) \
        .subquery()

    # Get divisions where player2 played in the season
    player2_divisions = Division.query \
        .join(Result, Division.id == Result.division_id) \
        .filter(
        Result.player_id == player2_id,
        Division.season_id == season_id
    ) \
        .subquery()

    # Find common divisions
    common_divisions = Division.query \
        .join(player1_divisions, Division.id == player1_divisions.c.id) \
        .join(player2_divisions, Division.id == player2_divisions.c.id) \
        .all()

    return common_divisions

def get_lowest_division_in_season(player1_id, player2_id, season_id):
    player1_divisions = Division.query \
        .join(Result, Division.id == Result.division_id) \
        .filter(
        Result.player_id == player1_id,
        Division.season_id == season_id
    ) \
        .all()

    # Get divisions where player2 played in the season
    player2_divisions = Division.query \
        .join(Result, Division.id == Result.division_id) \
        .filter(
        Result.player_id == player2_id,
        Division.season_id == season_id
    ) \
        .all()

    max_priority = 0
    if len(player1_divisions) > 0 and len(player2_divisions)>0: # both players should have at least 1 result in season
        for d in player1_divisions:
            if d.priority > max_priority:
                max_d = d
                max_priority = d.priority

        return max_d


def get_player_match_history(player_id, limit=10):
    """Get player's match history with opponent details"""
    matches = Match.query.filter(
        ((Match.player1_id == player_id) | (Match.player2_id == player_id))
    ) \
        .join(Division, Match.division_id == Division.id) \
        .join(Season, Division.season_id == Season.id) \
        .options(
        db.joinedload(Match.player1),
        db.joinedload(Match.player2),
        db.joinedload(Match.division).joinedload(Division.season_ref)
    ) \
        .order_by(Match.date_played.desc()) \
        .limit(limit) \
        .all()

    # Format match data
    match_history = []
    for match in matches:
        is_player1 = match.player1_id == player_id

        if is_player1:
            opponent = match.player2
            opponent_score = match.set1_player2
            player_score = match.set1_player1
        else:
            opponent = match.player1
            opponent_score = match.set1_player1
            player_score = match.set1_player2

        match_history.append({
            'match': match,
            'opponent': opponent,
            'is_winner': match.winner_id == player_id,
            'player_score': player_score,
            'opponent_score': opponent_score,
            'score_summary': match.score_summary,
            'date': match.date_played,
            'division': match.division.name,
            'season': match.division.season_ref.name,
            'year': match.division.season_ref.year,
        })

    return match_history


def get_player_opponents(player_id):
    """Get all opponents the player has played against"""
    opponents = db.session.query(Player).distinct() \
        .join(Match, ((Player.id == Match.player1_id) | (Player.id == Match.player2_id))) \
        .filter(
        ((Match.player1_id == player_id) | (Match.player2_id == player_id)),
        Player.id != player_id
    ) \
        .order_by(Player.last_name, Player.first_name) \
        .all()

    return opponents


def get_player_seasons(player_id):
    """Get all seasons the player has participated in"""
    seasons = db.session.query(Season).distinct() \
        .join(Division, Season.id == Division.season_id) \
        .join(Match, Division.id == Match.division_id) \
        .filter(
        ((Match.player1_id == player_id) | (Match.player2_id == player_id))
    ) \
        .order_by(Season.year.desc()) \
        .all()

    return seasons


def get_player_divisions(player_id):
    """Get all divisions the player has played in"""
    divisions = db.session.query(Division).distinct() \
        .join(Match, Division.id == Match.division_id) \
        .filter(
        ((Match.player1_id == player_id) | (Match.player2_id == player_id))
    ) \
        .order_by(Division.priority) \
        .all()

    return divisions


def calculate_h2h_stats(player1_id, player2_id):
    """Calculate head-to-head statistics between two players"""
    # Get all matches between the two players
    matches = Match.query.filter(
        ((Match.player1_id == player1_id) & (Match.player2_id == player2_id)) |
        ((Match.player1_id == player2_id) & (Match.player2_id == player1_id))
    ).all()

    if not matches:
        return None

    player1_wins = 0
    player2_wins = 0
    total_sets_player1 = 0
    total_sets_player2 = 0
    total_games_player1 = 0
    total_games_player2 = 0

    for match in matches:
        is_player1_match_player1 = match.player1_id == player1_id

        if match.winner_id == player1_id:
            player1_wins += 1
        else:
            player2_wins += 1

        # Calculate set and game counts
        if is_player1_match_player1:
            sets_won = sum([
                1 if match.set1_player1 > match.set1_player2 else 0,
                1 if match.set2_player1 and match.set2_player1 > match.set2_player2 else 0,
                1 if match.set3_player1 and match.set3_player1 > match.set3_player2 else 0
            ])
            sets_lost = sum([
                1 if match.set1_player1 < match.set1_player2 else 0,
                1 if match.set2_player1 and match.set2_player1 < match.set2_player2 else 0,
                1 if match.set3_player1 and match.set3_player1 < match.set3_player2 else 0
            ])
            games_won = sum([
                match.set1_player1 or 0,
                match.set2_player1 or 0,
                match.set3_player1 or 0
            ])
            games_lost = sum([
                match.set1_player2 or 0,
                match.set2_player2 or 0,
                match.set3_player2 or 0
            ])
        else:
            sets_won = sum([
                1 if match.set1_player2 > match.set1_player1 else 0,
                1 if match.set2_player2 > match.set2_player1 else 0,
                1 if match.set3_player2 and match.set3_player2 > match.set3_player1 else 0
            ])
            sets_lost = sum([
                1 if match.set1_player2 < match.set1_player1 else 0,
                1 if match.set2_player2 < match.set2_player1 else 0,
                1 if match.set3_player2 and match.set3_player2 < match.set3_player1 else 0
            ])
            games_won = sum([
                match.set1_player2 or 0,
                match.set2_player2 or 0,
                match.set3_player2 or 0
            ])
            games_lost = sum([
                match.set1_player1 or 0,
                match.set2_player1 or 0,
                match.set3_player1 or 0
            ])

        total_sets_player1 += sets_won
        total_sets_player2 += sets_lost
        total_games_player1 += games_won
        total_games_player2 += games_lost

    return {
        'total_matches': len(matches),
        'player1_wins': player1_wins,
        'player2_wins': player2_wins,
        'win_percentage': (player1_wins / len(matches) * 100) if matches else 0,
        'sets': f"{total_sets_player1}-{total_sets_player2}",
        'games': f"{total_games_player1}-{total_games_player2}",
        'matches': matches[:10]  # First 10 matches for details
    }

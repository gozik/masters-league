# tests/conftest.py
import os
import sys
import tempfile
import pytest
from datetime import datetime, date

# Add the parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app as real_app
from extensions import db
from models import League, Season, Division, Player, Result


@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    # Create a temporary file to isolate the database for each test
    db_fd, db_path = tempfile.mkstemp()

    # Create the app with common test config
    app = real_app
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'WTF_CSRF_ENABLED': False,
        'SERVER_NAME': 'localhost'  # Add this for URL building
    })

    # Create the database and load test data
    with app.app_context():
        db.create_all()
        load_test_data(db)

    yield app

    # Close and remove the temporary database
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    """A test client for the app."""
    with app.app_context():
        # Ensure we're in app context when yielding client
        yield app.test_client()


@pytest.fixture
def runner(app):
    """A test runner for the app."""
    return app.test_cli_runner()


def load_test_data(db_session):
    """Load minimal test data for testing."""
    # Create a test league
    league = League(name='Test League')
    db_session.session.add(league)
    db_session.session.commit()

    # Create test seasons
    seasons = []
    for i in range(1, 4):
        season = Season(
            name=f'Season {i}',
            year=2024,
            is_ranked=True,
            is_completed=True,
            date_start=date(2024, i, 1),
            date_end=date(2024, i, 28),
            league_id=league.id
        )
        db_session.session.add(season)
        seasons.append(season)

    db_session.session.commit()

    # Create test divisions
    divisions = []
    for i, season in enumerate(seasons):
        for j in range(1, 3):  # 2 divisions per season
            division = Division(
                name=f'M{j}',
                priority=100 + j * 10,
                season_id=season.id
            )
            db_session.session.add(division)
            divisions.append(division)

    db_session.session.commit()

    # Create test players
    players = []
    for i in range(1, 6):  # 5 players
        player = Player(
            first_name=f'Player{i}',
            last_name=f'Test{i}',
            gender='male' if i % 2 == 0 else 'female'
        )
        db_session.session.add(player)
        players.append(player)

    db_session.session.commit()

    # Create test results
    for division in divisions:
        for i, player in enumerate(players):
            result = Result(
                player_id=player.id,
                position=i + 1,
                match_count=5,
                win_count=4 - i,
                tie_win_count=0,
                set_diff=3 - i,
                game_diff=10 - i * 2,
                division_id=division.id,
                relegation='promoted' if i == 0 else 'unchanged' if i < 3 else 'relegated'
            )
            db_session.session.add(result)

    db_session.session.commit()
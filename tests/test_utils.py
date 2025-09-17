# tests/test_utils.py
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, date
from models import get_last_result_before_date


def test_get_last_result_before_date(app):
    """Test get_last_result_before_date function."""
    with app.app_context():
        # Create test data
        from models import Player, Season, Division, Result
        from extensions import db

        player = Player(first_name='Test', last_name='Utils', gender='male')
        db.session.add(player)
        db.session.commit()

        season = Season(
            name='Test Season',
            year=2024,
            is_ranked=True,
            is_completed=True,
            date_start=date(2024, 1, 1),  # Use date object
            date_end=date(2024, 1, 31),  # Use date object
            league_id=1
        )
        db.session.add(season)
        db.session.commit()

        division = Division(
            name='Test Division',
            priority=100,
            season_id=season.id
        )
        db.session.add(division)
        db.session.commit()

        # Create a result
        result = Result(
            player_id=player.id,
            position=1,
            match_count=5,
            win_count=4,
            division_id=division.id,
            relegation='promoted'
        )
        db.session.add(result)
        db.session.commit()

        # Test the function - use datetime object
        target_date = datetime(2024, 2, 1)
        last_result = get_last_result_before_date(
            player.id,
            target_date,
            'ranked',
            365
        )

        assert last_result is not None
        assert last_result.player_id == player.id
        assert last_result.position == 1


def test_get_last_result_before_date_no_results(app):
    """Test get_last_result_before_date with no matching results."""
    with app.app_context():
        # Create a new player with no results
        from models import Player
        from extensions import db

        player = Player(first_name='No', last_name='Results', gender='male')
        db.session.add(player)
        db.session.commit()

        target_date = datetime(2024, 2, 1)
        last_result = get_last_result_before_date(
            player.id,
            target_date,
            'ranked',
            365
        )

        assert last_result is None


def test_get_last_result_before_date_expired(app):
    """Test get_last_result_before_date with expired results."""
    with app.app_context():
        from models import Player, Season, Division, Result
        from extensions import db

        player = Player(first_name='Test', last_name='Expired', gender='male')
        db.session.add(player)
        db.session.commit()

        # Create an old season (more than 365 days)
        old_season = Season(
            name='Old Season',
            year=2022,
            is_ranked=True,
            is_completed=True,
            date_start=date(2022, 1, 1),  # Use date object
            date_end=date(2022, 1, 31),  # Use date object
            league_id=1
        )
        db.session.add(old_season)
        db.session.commit()

        old_division = Division(
            name='Old Division',
            priority=100,
            season_id=old_season.id
        )
        db.session.add(old_division)
        db.session.commit()

        old_result = Result(
            player_id=player.id,
            position=1,
            match_count=5,
            win_count=4,
            division_id=old_division.id,
            relegation='promoted'
        )
        db.session.add(old_result)
        db.session.commit()

        # Test with short expire_days (should not find the old result)
        target_date = datetime(2024, 2, 1)
        last_result = get_last_result_before_date(
            player.id,
            target_date,
            'ranked',
            30  # Only 30 days expiry
        )

        # Should not find the old result because it's expired
        assert last_result is None
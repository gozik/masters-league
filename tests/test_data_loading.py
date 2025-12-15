# tests/test_data_loading.py
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from io import StringIO
from app import input_data_from_json, delete_all, reset_content
from extensions import db
from models import League, Season, Division, Player, Result, Ranking


def test_input_data_from_json(client, app):
    """Test input_data_from_json function."""
    # Create test JSON data
    test_data = {
        "Test League": [
            {
                "name": "Test Season",
                "year": 2024,
                "date_start": "2024-01-01",
                "date_end": "2024-01-31",
                "is_ranked": True,
                "divisions": [
                    {
                        "name": "Test Division",
                        "priority": 100,
                        "results": [
                            {
                                "first_name": "Test",
                                "last_name": "Player",
                                "gender": "male",
                                "position": 1,
                                "match_count": 5,
                                "win_count": 4,
                                "tie_win_count": 0,
                                "set_diff": 3,
                                "game_diff": 10,
                                "relegation": "promoted"
                            }
                        ]
                    }
                ]
            }
        ]
    }

    # Convert to file-like object
    json_file = StringIO(json.dumps(test_data))

    with app.app_context():
        # Delete existing data
        delete_all()

        # Load the data
        input_data_from_json(json_file)

        assert League.query.count() == 1
        assert Season.query.count() == 1
        assert Division.query.count() == 1
        assert Player.query.count() == 1
        assert Result.query.count() == 1

        league = League.query.first()
        assert league.name == "Test League"

        player = Player.query.first()
        assert player.first_name == "Test"
        assert player.last_name == "Player"


def test_delete_all(client, app):
    """Test delete_all function."""
    with app.app_context():

        player = Player(first_name='Test', last_name='Delete')
        db.session.add(player)
        db.session.commit()

        assert Player.query.count() > 0

        # Delete all data
        delete_all()

        # Verify data was deleted
        assert Player.query.count() == 0

        player = Player(first_name='Test', last_name='Delete')
        db.session.add(player)
        db.session.commit()

        assert Player.query.count() == 1


def test_content_reset(client, app):
    with app.app_context():
        reset_content()

        assert League.query.count() == 1
        assert Season.query.count() == 10
        assert Division.query.count() == 30
        assert Player.query.count() == 108
        assert Result.query.count() == 295
        assert Ranking.query.count() == 456


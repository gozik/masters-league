# tests/test_data_loading.py
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from io import StringIO
from app import input_data_from_json, delete_all
from extensions import db


def test_input_data_from_json(app):
    """Test input_data_from_json function."""
    with app.app_context():
        # Delete existing data
        delete_all()

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

        # Load the data
        input_data_from_json(json_file)

        # Verify the data was loaded correctly
        from models import League, Season, Division, Player, Result
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


def test_delete_all(app):
    """Test delete_all function."""
    with app.app_context():
        # Add some test data
        from models import Player

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
# tests/test_models.py
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Player, League, Season, Division, Result, Ranking, get_division_name


def test_get_division_name():
    """Test division name calculation based on priority."""
    assert get_division_name(105) == 'M1'
    assert get_division_name(115) == 'M2'
    assert get_division_name(125) == 'M3'
    assert get_division_name(135) == 'M4'
    assert get_division_name(205) == 'O1'
    assert get_division_name(215) == 'O2'


def test_player_model():
    """Test Player model creation and relationships."""
    player = Player(first_name='Test', last_name='Player', gender='male')
    assert player.first_name == 'Test'
    assert player.last_name == 'Player'
    assert player.gender == 'male'
    assert str(player) == '<Test Player>'


def test_league_model():
    """Test League model creation."""
    league = League(name='Test League')
    assert league.name == 'Test League'
    assert str(league) == '<Test League League>'


def test_season_model():
    """Test Season model creation."""
    season = Season(
        name='Test Season',
        year=2024,
        is_ranked=True,
        is_completed=True
    )
    assert season.name == 'Test Season'
    assert season.year == 2024
    assert season.is_ranked == True
    assert str(season) == '<Season Test Season (2024)>'


def test_division_model():
    """Test Division model creation."""
    division = Division(name='Test Division', priority=100)
    assert division.name == 'Test Division'
    assert division.priority == 100
    assert str(division) == '<Division Test Division>'


def test_result_model():
    """Test Result model creation and methods."""

    result = Result(
        position=1,
        match_count=5,
        win_count=4,
        tie_win_count=0,
        set_diff=3,
        game_diff=10
    )

    # Set the mock division
    result.division_ref = Division(priority=110)

    assert result.position == 1
    assert result.match_count == 5
    assert result.win_count == 4

    # Test calc_new_priority method
    result.relegation = 'promoted'
    assert result.calc_new_priority() == 100

    result.relegation = 'relegated'
    assert result.calc_new_priority() == 120

    result.relegation = 'double promoted'
    assert result.calc_new_priority() == 90


def test_ranking_model():
    """Test Ranking model creation."""
    ranking = Ranking(position=1)
    assert ranking.position == 1


def test_player_to_dict():
    """Test Player to_dict method."""
    player = Player(first_name='Test', last_name='Player')
    player_dict = player.to_dict()
    assert player_dict['first_name'] == 'Test'
    assert player_dict['last_name'] == 'Player'


def test_season_to_dict():
    """Test Season to_dict method."""
    season = Season(name='Test', year=2024)
    season_dict = season.to_dict()
    assert season_dict['name'] == 'Test'
    assert season_dict['year'] == 2024
# tests/test_routes.py
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_index_route(client, app):
    """Test the index route returns 200."""
    #with app.app_context():
    response = client.get('/')
    assert response.status_code == 200
    assert b'Tashkent Masters League' in response.data


def test_rankings_route(client, app):
    """Test the rankings route returns 200."""
    with app.app_context():
        response = client.get('/rankings')
        assert response.status_code == 200
        assert bytes('Рейтинг лиги', 'utf-8') in response.data


def test_results_route(client, app):
    """Test the results route returns 200."""
    with app.app_context():
        response = client.get('/results')
        assert response.status_code == 200
        assert bytes('Итоги сезонов', 'utf-8') in response.data


def test_regulations_route(client, app):
    """Test the regulations route returns 200."""
    with app.app_context():
        response = client.get('/regulations')
        assert response.status_code == 200
        assert bytes('Регламент лиги', 'utf-8') in response.data


def test_faq_route(client, app):
    """Test the FAQ route returns 200."""
    with app.app_context():
        response = client.get('/faq')
        assert response.status_code == 200
        assert bytes('Часто задаваемые вопросы', 'utf-8') in response.data


def test_schedule_route(client, app):
    """Test the schedule route returns 200."""
    with app.app_context():
        response = client.get('/schedule')
        assert response.status_code == 200
        assert bytes('Календарь', 'utf-8') in response.data


def test_application_route(client, app):
    """Test the application route returns 200."""
    with app.app_context():
        response = client.get('/application')
        assert response.status_code == 200
        assert bytes('Заявка', 'utf-8') in response.data


def test_player_profile_route(client, app):
    """Test player profile route with existing player."""
    with app.app_context():
        from models import Player
        # Get the first player from test data
        player = Player.query.first()
        assert player is not None

        response = client.get(f'/player/{player.id}')
        assert response.status_code == 200
        assert bytes('Профиль Игрока', 'utf-8') in response.data


def test_player_profile_route_404(client, app):
    """Test player profile route with non-existent player returns 404."""
    with app.app_context():
        response = client.get('/player/9999')
        assert response.status_code == 404


def test_season_rules_route(client, app):
    """Test season rules route."""
    with app.app_context():
        from models import Season
        season = Season.query.first()
        assert season is not None

        response = client.get(f'/season/{season.id}/rules')
        assert response.status_code == 200
        assert bytes('Правила сезона', 'utf-8') in response.data


def test_rankings_with_season_filter(client, app):
    """Test rankings route with season filter."""
    with app.app_context():
        from models import Season
        season = Season.query.first()
        assert season is not None

        response = client.get(f'/rankings?season_id={season.id}')
        assert response.status_code == 200


def test_results_with_filters(client, app):
    """Test results route with filters."""
    with app.app_context():
        from models import Season, Division
        season = Season.query.first()
        division = Division.query.first()
        assert season is not None
        assert division is not None

        response = client.get(f'/results?season_id={season.id}&division_id={division.id}')
        assert response.status_code == 200


def test_application_with_division_filter(client, app):
    """Test application route with division filter."""
    with app.app_context():
        response = client.get('/application?division_name=M1')
        assert response.status_code == 200
from flask import render_template, request, current_app
from init import create_app
from models import Player, League, Season, Division, Result, Ranking, get_last_result_before_date
from data.seasons_data import init_seasons_data
from extensions import db
import json
from datetime import datetime
import os
import csv

app = create_app()


def delete_all():
    Ranking.query.delete()
    Result.query.delete()
    Player.query.delete()
    Division.query.delete()
    Season.query.delete()
    League.query.delete()

    db.session.commit()
    return


def input_data_from_json(file):
    """Add all leagues, seasons, divisions, players, results from file.

    Must be invoked within app_context.
    This function now performs the import within a single transaction to avoid
    per-object commits and to ensure atomicity.
    """
    d = json.load(file)

    # Use a transaction: either everything is committed, or rolled back on error
    with db.session.begin():
        # Cache existing players to reduce queries for repeated names
        existing_players = {}
        for p in Player.query.all():
            key = (p.first_name.strip(), p.last_name.strip())
            existing_players[key] = p

        for league_name, seasons_list in d.items():
            league = League(name=league_name)
            db.session.add(league)
            db.session.flush()

            for s in seasons_list:
                season = Season(
                    name=s.get('name'),
                    year=s.get('year'),
                    league_id=league.id,
                    date_start=datetime.strptime(s['date_start'], "%Y-%m-%d") if s.get('date_start') else None,
                    date_end=datetime.strptime(s['date_end'], "%Y-%m-%d") if s.get('date_end') else None,
                    is_ranked=True
                )

                if 'is_ranked' in s and s['is_ranked'] in (0, "0", False, "false", "False"):
                    season.is_ranked = False

                db.session.add(season)
                db.session.flush()

                for div in s.get('divisions', []):
                    division = Division(
                        name=div.get('name'),
                        priority=div.get('priority'),
                        season_id=season.id
                    )
                    db.session.add(division)
                    db.session.flush()

                    for r in div.get('results', []):
                        first = r.get('first_name', '').strip()
                        last = r.get('last_name', '').strip()
                        player_key = (first, last)

                        player = existing_players.get(player_key)
                        if player is None:
                            player = Player(first_name=first, last_name=last, gender=r.get('gender'))
                            db.session.add(player)
                            # flush to get player.id for dependent objects
                            db.session.flush()
                            existing_players[player_key] = player

                        result = Result(
                            player_id=player.id,
                            position=r.get('position'),
                            match_count=r.get('match_count'),
                            win_count=r.get('win_count'),
                            tie_win_count=r.get('tie_win_count'),
                            set_diff=r.get('set_diff'),
                            game_diff=r.get('game_diff'),
                            division_id=division.id,
                            relegation=r.get('relegation')
                        )
                        db.session.add(result)

    # end of transaction block will commit if no exception occurred
    return


def calculate_rankings(date):
    """
    Calculate rankings for given date
    """
    results = []

    for player in Player.query.all():
        last_result = get_last_result_before_date(player.id, date, filter_seasons='ranked', expire_days=365)

        if not last_result:
            continue

        prev_priority = last_result.division_ref.priority
        position = last_result.position
        result_date = last_result.division_ref.season_ref.date_end

        new_priority = last_result.calc_new_priority()

        results.append({'last_result': last_result,
                        'new_priority': new_priority,
                        'prev_priority': prev_priority,
                        'position': position,
                        'result_date': result_date,
                        'player': player})

    sorted_items = sorted(
        results,
        key=lambda x: (
            x['new_priority'],  # (ascending)
            x['prev_priority'],  # (ascending)
            x['position'],  # (ascending)
            -(x['result_date'].toordinal())  # (descending)
        )
    )

    rankings = []
    for i, value in enumerate(sorted_items):
        ranking = Ranking(player_id=value['player'].id,
                          position=i + 1,
                          actual_date=date,
                          actual_season_id=value['last_result'].division_ref.season_id,
                          last_result_id=value['last_result'].id)

        rankings.append(ranking)

        db.session.add(ranking)

    db.session.commit()

    return rankings


def reset_content():
    # must be invoked inside app context
    delete_all()

    actual_results_path = current_app.config.get('ACTUAL_RESULTS_JSON', 'data/actual_results.json')
    with open(actual_results_path) as f:
        input_data_from_json(f)

    seasons = Season.query.order_by('date_end').all()
    for s in seasons:
        if s.is_ranked:
            calculate_rankings(s.date_end)

    init_seasons_data()


@app.template_filter('to_date')
def to_date_filter(date_string):
    try:
        return datetime.strptime(date_string, '%Y-%m-%d').date()
    except ValueError:
        return None


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/rankings')
def show_rankings():
    """Display rankings with date and season filtering"""
    latest_season = Season.query.filter(Season.is_completed == True, Season.is_ranked == True) \
        .order_by(Season.date_end.desc()).first()

    if not latest_season:
        # handle empty DB gracefully
        return render_template('rankings.html', actual_date=None, rankings=[], seasons=[], selected_season_id=None)

    actual_date = latest_season.date_end

    # Get filters from request
    season_id = request.args.get('season_id', type=int)
    if season_id:
        season = db.session.get(Season, season_id)
        if season:
            actual_date = season.date_end

    # Get available seasons for dropdown
    seasons = Season.query.order_by(Season.id.desc()).filter(Season.is_ranked == True) \
        .filter(Season.is_completed == True).all()

    # Get rankings
    rankings = Ranking.query.filter_by(actual_date=actual_date).order_by('position').all()
    rankings_data = [p.to_dict() for p in rankings]

    return render_template('rankings.html',
                           actual_date=actual_date,
                           rankings=rankings_data,
                           seasons=seasons,
                           selected_season_id=season_id)


@app.route('/results')
def show_results():
    # Get filters from request
    season_id = request.args.get('season_id', type=int)
    division_id = request.args.get('division_id', type=int)

    divisions = []
    if season_id:
        results = Result.query.join(Result.division_ref).filter(Division.season_id == season_id).all()
        divisions = db.session.get(Season, season_id).divisions
        if division_id:
            results = Result.query.filter_by(division_id=division_id).all()
    else:
        results = Result.query.all()

    results_data = [p.to_dict() for p in results]

    seasons = Season.query.filter(Season.is_completed == True).order_by(Season.id.desc()).all()

    return render_template('results.html', results=results_data, seasons=seasons, selected_season_id=season_id,
                           divisions=divisions, selected_division_id=division_id)


@app.route('/application')
def show_season_application():
    """Display players in season application"""
    division_name = request.args.get('division_name', type=str)

    with open('data/application_list_season254.csv') as f:
        csv_reader = csv.DictReader(f)

        players = []

        for row in csv_reader:
            player_str = row['Player']
            raketo_rating = row['Rating']
            wildcard = row['Wildcard']

            player_name = player_str.partition(' ')[2]
            player_surname = player_str.partition(' ')[0]

            player_dict = {'player_name': player_str, 'raketo_rating': raketo_rating, 'wildcard': wildcard}
            player_dict['player_id'] = 0

            player = Player.query.filter(
                (Player.first_name == player_name) & (Player.last_name == player_surname)).first()
            if player:
                ranking = Ranking.query.filter(Ranking.player_id == player.id).order_by(
                    Ranking.actual_date.desc()).first()
                player_dict['player_id'] = player.id
                if ranking:
                    player_dict['ranking'] = ranking.to_dict()['position']
                    player_dict['qualification'] = ranking.to_dict()['new_division']

            else:
                player_dict['qualification'] = 'NEW'

            # calculate division
            player_dict['division'] = player_dict['qualification']

            if player_dict['division'] == 'NEW':
                if player_dict['raketo_rating'] > '3.1':
                    player_dict['division'] = 'M4'
                else:
                    player_dict['division'] = 'M4'

            if player_dict['wildcard'] != '':
                player_dict['division'] = player_dict['wildcard']

            players.append(player_dict)

    players_count = len(players)

    if division_name:
        players = [player for player in players if player['division'].startswith(division_name)]

    players = sorted(players, key=lambda plr: (
        plr['division'], plr['ranking'] if 'ranking' in plr else (1000 - float(plr['raketo_rating']))))

    selected_player_count = len(players)

    divisions = ['M1', 'M2', 'M3', 'M4']

    return render_template('application.html', players=players, count=players_count, division_name=division_name,
                           divisions=divisions, selected_player_count=selected_player_count)


@app.route('/regulations')
def show_regulations():
    current_year = current_app.config.get('ACTIVE_SEASON_YEAR')
    current_name = current_app.config.get('ACTIVE_SEASON_NAME')

    seasons = Season.query.filter(Season.is_completed == True).order_by(Season.id.desc()).all()

    current_season = Season.query.filter_by(year=current_year, name=current_name).order_by(Season.id.desc()).first()

    return render_template('regulations.html', seasons=seasons, current_season=current_season)


@app.route('/faq')
def faq():
    return render_template('faq.html')


@app.route('/schedule')
def show_schedule():
    current_year = current_app.config.get('ACTIVE_SEASON_YEAR')

    seasons = Season.query.filter_by(year=current_year).order_by('date_start').all()

    return render_template('schedule.html', seasons=seasons, current_year=current_year)


@app.route('/player/<int:player_id>')
def player_profile(player_id):
    """Display player profile with statistics and history"""
    player = db.get_or_404(Player, player_id)

    # Get current ranking
    current_ranking = get_current_ranking(player_id)

    # Get season results
    season_results = get_results(player_id)

    # Calculate total statistics
    total_stats = calculate_total_stats(player_id)

    return render_template('player_profile.html',
                           player=player,
                           current_ranking=current_ranking,
                           season_results=season_results,
                           division_history=season_results,
                           total_stats=total_stats,
                           )


@app.route('/season/<season_id>/rules')
def season_rules(season_id):
    season = db.get_or_404(Season, season_id)

    season_info = season.to_dict()

    return render_template('season_rules.html', season=season, season_info=season_info)


def get_current_ranking(player_id):
    """Get player's current ranking"""
    return Ranking.query.filter_by(player_id=player_id).order_by(Ranking.actual_date.desc()).first()


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


if __name__ == '__main__':
    with app.app_context():
        db.create_all()

        if not League.query.first() or app.config.get('DEBUG'):  # always reseting content in dev
            reset_content()

    # Use config-driven debug mode
    app.run(debug=app.config.get('DEBUG', False), host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

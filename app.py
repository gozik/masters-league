from flask import render_template, request, current_app, jsonify
from init import create_app
from models import Player, League, Season, Division, Result, Ranking, get_last_result_before_date, get_current_ranking, \
    get_results, calculate_total_stats, get_season_by_raketo_name, get_common_divisions_in_season, \
    get_lowest_division_in_season, parse_score, Match, get_player_match_history, get_player_opponents, \
    get_player_seasons, calculate_h2h_stats
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
    Match.query.delete()

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

def import_matches_from_csv(file_path, batch_size=50):
    """
    Import matches from CSV file to database
    """
    imported_count = 0
    skipped_count = 0
    error_count = 0

    existing_players = {}
    for p in Player.query.all():
        key = p.last_name.strip() + ' ' + p.first_name.strip()
        existing_players[key] = p

    with open(file_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)

        for i, row in enumerate(reader):
            try:
                # Parse data from row
                winner_name = row.get('winner', '').strip()
                loser_name = row.get('loser', '').strip()
                score = row.get('score', '').strip()
                season_name = row.get('season', '').strip()
                date_str = row.get('date', '').strip()

                # Skip rows with missing essential data
                if not all([winner_name, loser_name, score, season_name, date_str]):
                    print(f"Skipping row {i}: Missing essential data")
                    skipped_count += 1
                    continue

                # Parse date
                try:
                    match_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                except ValueError:
                    print(f"Skipping row {i}: Invalid date format: {date_str}")
                    skipped_count += 1
                    continue

                if winner_name not in existing_players or loser_name not in existing_players:
                    print(f"Skipping row {i}: Unknown player: {winner_name} vs {loser_name}")
                    skipped_count += 1
                    continue

                # Get or create players
                winner = existing_players[winner_name]
                loser = existing_players[loser_name]

                # Get season
                season = get_season_by_raketo_name(season_name)
                if not season:
                    print(f"Skipping row {i}: Unknown season: {season_name}")
                    skipped_count += 1
                    continue


                # Get division
                divisions = get_common_divisions_in_season(winner.id, loser.id, season.id)
                if len(divisions) == 0:
                    divisions = [get_lowest_division_in_season(winner.id, loser.id, season.id)]
                if len(divisions) == 0:
                    print(f"Skipping row {i}: No common divisions in {season_name} for {winner_name} vs {loser_name}")
                    skipped_count += 1
                    continue


                division = divisions[0]
                for d in divisions:
                    if division.priority < d.priority:
                        division = d # select max priority division if there were several common ones

                # Parse score
                parsed_score = parse_score(score)
                if not parsed_score:
                    print(f"Skipping row {i}: Could not parse score: {score}")
                    skipped_count += 1
                    continue

                # Create match record
                match = Match(
                    date_played=match_date,
                    season_id=season.id,
                    division_id=division.id,
                    player1_id=winner.id,  # Winner is player1
                    player2_id=loser.id,  # Loser is player2
                    winner_id=winner.id,
                )

                # Set score based on parsed structure
                sets = parsed_score['sets']
                # Game in sets

                # Set 1
                if len(sets) > 0:
                    match.set1_player1 = sets[0]['player1']  # Winner's games
                    match.set1_player2 = sets[0]['player2']  # Loser's games
                    if sets[0]['tiebreak']:
                        match.tb1_player1 = sets[0]['tiebreak_score']['player1']
                        match.tb1_player2 = sets[0]['tiebreak_score']['player2']

                # Set 2
                if len(sets) > 1:
                    match.set2_player1 = sets[1]['player1']
                    match.set2_player2 = sets[1]['player2']
                    if sets[1]['tiebreak']:
                        match.tb2_player1 = sets[1]['tiebreak_score']['player1']
                        match.tb2_player2 = sets[1]['tiebreak_score']['player2']

                # Set 3 (if exists and not royal tiebreak)
                if len(sets) > 2 and not parsed_score['royal_tiebreak']:
                    match.set3_player1 = sets[2]['player1']
                    match.set3_player2 = sets[2]['player2']
                    if sets[2]['tiebreak']:
                        match.tb3_player1 = sets[2]['tiebreak_score']['player1']
                        match.tb3_player2 = sets[2]['tiebreak_score']['player2']

                # Royal tiebreak
                if parsed_score['royal_tiebreak'] and parsed_score['royal_tiebreak_score']:
                    match.royal_tiebreak_player1 = parsed_score['royal_tiebreak_score'][0]  # Winner's points
                    match.royal_tiebreak_player2 = parsed_score['royal_tiebreak_score'][1]  # Loser's points

                db.session.add(match)
                imported_count += 1

                # Commit in batches for performance
                if imported_count % batch_size == 0:
                    db.session.commit()
                    print(f"Imported {imported_count} matches...")

            except Exception as e:
                error_count += 1
                print(f"Error importing row {i}: {str(e)}")
                print(f"Row data: {row}")
                db.session.rollback()
                continue

        # Final commit
        try:
            db.session.commit()
            print(f"\nImport completed!")
            print(f"Successfully imported: {imported_count}")
            print(f"Skipped: {skipped_count}")
            print(f"Errors: {error_count}")
        except Exception as e:
            db.session.rollback()
            print(f"Final commit failed: {str(e)}")

    return {
        'imported': imported_count,
        'skipped': skipped_count,
        'errors': error_count
    }


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

    import_matches_from_csv('data/all_matches.csv')


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

    seasons = Season.query.filter(Season.is_completed == True).order_by(Season.date_end.desc()).all()

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

    current_season = None
    if current_name:
        current_season = Season.query.filter_by(year=current_year, name=current_name).order_by(Season.id.desc()).first()


    return render_template('regulations.html', seasons=seasons, current_season=current_season, year=current_year)


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

    # Get match history (last 10 matches)
    match_history = get_player_match_history(player_id, limit=12)

    return render_template('player_profile.html',
                           player=player,
                           current_ranking=current_ranking,
                           season_results=season_results,
                           division_history=season_results,
                           total_stats=total_stats,
                           match_history=match_history)


@app.route('/player/<int:player_id>/matches')
def player_matches(player_id):
    """Display all matches for a player with opponent filtering"""
    player = db.get_or_404(Player, player_id)

    # Get filter parameters
    opponent_id = request.args.get('opponent_id', type=int)
    season_id = request.args.get('season_id', type=int)
    page = request.args.get('page', 1, type=int)
    per_page = 50

    # Build base query
    base_query = Match.query.filter(
        ((Match.player1_id == player_id) | (Match.player2_id == player_id))
    )

    # Apply opponent filter
    if opponent_id:
        base_query = base_query.filter(
            ((Match.player1_id == opponent_id) & (Match.player2_id == player_id)) |
            ((Match.player1_id == player_id) & (Match.player2_id == opponent_id))
        )

    # Apply season filter
    if season_id:
        base_query = base_query.join(Division).filter(Division.season_id == season_id)
    else:
        base_query = base_query.join(Division)

    # Join related tables and order
    matches_query = base_query \
        .join(Season, Division.season_id == Season.id) \
        .options(
        db.joinedload(Match.player1),
        db.joinedload(Match.player2),
        db.joinedload(Match.division).joinedload(Division.season_ref)
    ) \
        .order_by(Match.date_played.desc())

    # Paginate
    pagination = matches_query.paginate(page=page, per_page=per_page, error_out=False)
    matches = pagination.items

    # Calculate H2H statistics if opponent filter is applied
    h2h_stats = None
    if opponent_id:
        opponent = db.session.get(Player, opponent_id)
        if opponent:
            h2h_stats = calculate_h2h_stats(player_id, opponent_id)

    # Format match data
    match_history = []
    for match in matches:
        is_player1 = match.player1_id == player_id

        if is_player1:
            opponent = match.player2
        else:
            opponent = match.player1


        match_history.append({
            'match': match,
            'opponent': opponent,
            'is_winner': match.winner_id == player_id,
            'score_summary': match.score_summary,
            'date': match.date_played,
            'division': match.division.name,
            'season': match.division.season_ref.name,
            'year': match.division.season_ref.year
        })

    # Get filter options
    opponents = get_player_opponents(player_id)
    seasons = get_player_seasons(player_id)

    return render_template('player_matches.html',
                           player=player,
                           match_history=match_history,
                           pagination=pagination,
                           h2h_stats=h2h_stats,
                           opponents=opponents,
                           seasons=seasons,
                           selected_opponent_id=opponent_id,
                           selected_season_id=season_id,
                           )


@app.route('/api/search-players')
def search_players():
    query = request.args.get('q', '').lower().strip()

    if not query or len(query) < 2:
        return jsonify([])

    try:
        # Search in database - adjust based on your Player model
        players = Player.query.filter(
            (Player.first_name.ilike(f'%{query}%')) |
            (Player.last_name.ilike(f'%{query}%'))
        ).limit(10).all()

        results = [{
            'id': p.id,
            'first_name': p.first_name,
            'last_name': p.last_name,
            'current_rating': p.current_ranking or '-'
        } for p in players]

        return jsonify(results)

    except Exception as e:
        print(f"Search error: {e}")
        return jsonify([])


@app.route('/season/<season_id>/rules')
def season_rules(season_id):
    season = db.get_or_404(Season, season_id)

    season_info = season.to_dict()

    return render_template('season_rules.html', season=season, season_info=season_info)





if __name__ == '__main__':
    with app.app_context():
        db.create_all()

        if not League.query.first() or app.config.get('DEBUG'):  # always reseting content in dev
            reset_content()

    # Use config-driven debug mode
    app.run(debug=app.config.get('DEBUG', False), host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

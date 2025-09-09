##### Datenbank-Abfragen
import psycopg2

from vars import DB_LOGIN
import logging
import flask as f

def fetch_data(query: str, columns: list[str], params: tuple = None) -> tuple[list[dict] | None, None | str]:
    """Führt eine SQL-Abfrage aus und gibt die Ergebnisse zurück."""
    try:
        with psycopg2.connect(DB_LOGIN) as con:
            cur = con.cursor()
            cur.execute(query, params)
            rows = cur.fetchall()
            result = [dict(zip(columns, row)) for row in rows]
            return result, None
    except Exception as e:
        return None, str(e)

def execute_query(query: str, params: tuple = None) -> tuple[bool, str | None]:
    """Führt SQL-Befehle aus, die keine Ergebnisse zurückgeben (CREATE, INSERT, UPDATE, DELETE)"""
    try:
        with psycopg2.connect(DB_LOGIN) as con:
            cur = con.cursor()
            cur.execute(query, params)
            con.commit()
            return True, None
    except Exception as e:
        return False, str(e)

def save_match(data: dict, team_id: int) -> tuple[str | None, None | int]:
    """Speichert alle Daten eines Matches in der Datenbank.
    Args:
        data (dict): Ein Dictionary mit allen Match-Daten. Siehe extractData.py für das Format.
        team_id (int): Die ID des Teams, dem das Match zugeordnet werden soll.
    
    Returns:
        tuple[str | None, None | int]: Eine Erfolgsmeldung und der HTTP-Statuscode oder None und ein Fehlercode.
    """

    success, error = execute_query("BEGIN TRANSACTION;")
    if error:
        logging.error(f"Database error during initialization [BEGIN TRANSACTION]: {error}")
        f.abort(500, description="Internal Server Error")

    # region Check if Match already exists
    match_id = data["match_data"].get("match_id")
    query = "SELECT match_id FROM Matches WHERE match_id = %s;"
    params = (match_id,)
    result, error = fetch_data(query, ['match_id'], params)
    if error:
        logging.error(f"Database error during match existence check: {error}")
        execute_query("ROLLBACK;")
        f.abort(500, description="Internal Server Error")

    if result:  # Wenn Liste nicht leer ist
        logging.info(f"Match {match_id} already exists with ID {result[0]['match_id']}.")
        data["match_data"]["match.id"] = result[0]['match_id']
        f.abort(409, description="Conflict: Match already exists.")
    else:  # Wenn Liste leer ist (Match existiert nicht)
        logging.info(f"Match {match_id} does not exist yet.")
        execute_query("ROLLBACK;")
    # endregion

    # region Save Player
    for ubisoft_id, player_data in data["player_data"].items():
        query = """
            INSERT INTO player (ubisoft_id, username, timestamp, team_id)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (ubisoft_id, username, team_id) 
            DO UPDATE SET 
                timestamp = CASE 
                    WHEN EXCLUDED.timestamp > Player.timestamp THEN EXCLUDED.timestamp 
                    ELSE Player.timestamp 
                END
            RETURNING id;
        """

        params = (
            player_data.get('ubisoft_id'),
            player_data.get('username'), 
            player_data.get('timestamp'),
            team_id
        )

        result, error = fetch_data(query, ['id'], params)
        if error:
            logging.error(f"Database error during player insert/update: {error}")
            execute_query("ROLLBACK;")
            f.abort(500, description="Internal Server Error")

        player_id = result[0]['id'] if result else None
        
        if not player_id:
            logging.error(f"Failed to retrieve player ID after insert/update for Ubisoft ID {player_data.get('ubisoft_id')}")
            execute_query("ROLLBACK;")
            f.abort(500, description="Internal Server Error")
        else:
            data["player_data"][ubisoft_id]["player.id"] = player_id
    # endregion

    # region Save Match
    match_info = data["match_data"]
    query = """
    INSERT INTO matches (match_id, player_id, timestamp, game_mode, map, match_type,
    game_version, team_id, winner_team_index, team0_starting_side, prep_duration,
    round_duration, plant_duration)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    RETURNING match_id;
    """

    recording_player_ubisoft_id = match_info.get("player_id")
    recording_playerID = data["player_data"][recording_player_ubisoft_id]["player.id"]

    params = (
        match_info.get("match_id"),
        recording_playerID,
        match_info.get("timestamp"),
        match_info.get("game_mode"),
        match_info.get("map"),
        match_info.get("match_type"),
        match_info.get("game_version"),
        team_id,
        match_info.get("winner_team_index"),
        match_info.get("team0_starting_side"),
        match_info.get("prep_duration"),
        match_info.get("round_duration"),
        match_info.get("plant_duration"),
    )

    result, error = fetch_data(query, ['match_id'], params)

    if error:
        logging.error(f"Database error during match insert/update: {error}")
        execute_query("ROLLBACK;")
        f.abort(500, description="Internal Server Error")

    else:
        match_id = result[0]['match_id']
    # endregion
    
    # region Save rounds
    rounds_data = data["rounds_data"]
    for i, round_data in enumerate(rounds_data):
        query = """INSERT INTO rounds (match_id, round_number, site, winner_team_index, time_to_entry,
        atk_team_index, def_team_index, ok_team_index, ok_refrag, clutch, win_condition)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id;
        """

        params = (
            round_data.get("match_id"),
            round_data.get("round_number"),
            round_data.get("site"),
            round_data.get("winner_team_index"),
            round_data.get("time_to_entry"),
            round_data.get("atk_team_index"),
            round_data.get("def_team_index"),
            round_data.get("ok_team_index"),
            round_data.get("ok_refrag"),
            round_data.get("clutch"),
            round_data.get("win_condition"),
        )

        result, error = fetch_data(query, ['id'], params)
        if error:
            logging.error(f"Database error during round insert/update: {error}")
            execute_query("ROLLBACK;")
            f.abort(500, description="Internal Server Error")

        round_id = result[0]['id'] if result else None
        if not round_id:
            logging.error(f"Failed to retrieve round ID after insert/update for match ID {round_data.get('match_id')}")
            execute_query("ROLLBACK;")
            f.abort(500, description="Internal Server Error")

        rounds_data[i]["round.id"] = round_id
    # endregion

    # region Save playerRound
    player_round_data = data["player_rounds_data"]
    for round_dict in player_round_data:
        for ubisoft_id, dic in round_dict.items():
            query = """
            INSERT INTO playerround (player_id, round_id, team_index, operator, spawn, kills, death,
            headshots, plant, defuse, kostpoint, onevx, ok, od, win, atk, refrags, got_refraged)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id;
            """

            round_number = dic.get("round")
            roundID = rounds_data[round_number - 1]["round.id"]
            params = (
                data["player_data"][ubisoft_id]["player.id"],
                roundID,
                dic.get("team_index"),
                dic.get("operator"),
                dic.get("spawn"),
                dic.get("kills"),
                dic.get("death"),
                dic.get("headshots"),
                dic.get("plant"),
                dic.get("defuse"),
                dic.get("kost"),
                dic.get("onevx"),
                dic.get("ok"),
                dic.get("od"),
                dic.get("win"),
                dic.get("atk"),
                dic.get("refrags"),
                dic.get("got_refraged")
            )

            result, error = fetch_data(query, ['id'], params)
            if error:
                logging.error(f"Database error during playerRound insert/update: {error}")
                execute_query("ROLLBACK;")
                f.abort(500, description="Internal Server Error")

            player_round_id = result[0]['id'] if result else None
            if not player_round_id:
                logging.error(f"Failed to retrieve playerRound ID after insert/update for round ID {roundID}")
                execute_query("ROLLBACK;")
                f.abort(500, description="Internal Server Error")
    # endregion

    # region Save playerMatch
    player_match_data = data["player_match_data"]
    for ubisoft_id, dic in player_match_data.items():
        query = """
        INSERT INTO playermatch (player_id, match_id, team_index, kills, assists, deaths,
        headshots, kost, win, won_rounds, lost_rounds, won_atk_rounds, lost_atk_rounds,
        won_def_rounds, lost_def_rounds, oks, oks_atk, ods, ods_atk, refrags, got_refraged)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id;
        """

        params = (
            data["player_data"][ubisoft_id]["player.id"],
            dic.get("match_id"),
            dic.get("team_index"),
            dic.get("kills"),
            dic.get("assists"),
            dic.get("deaths"),
            dic.get("headshots"),
            dic.get("kost"),
            dic.get("win_match"),
            dic.get("won_rounds"),
            dic.get("lost_rounds"),
            dic.get("atk_won_rounds"),
            dic.get("atk_lost_rounds"),
            dic.get("def_won_rounds"),
            dic.get("def_lost_rounds"),
            dic.get("oks"),
            dic.get("oks_atk"),
            dic.get("ods"),
            dic.get("ods_atk"),
            dic.get("refrags"),
            dic.get("got_refraged")
        )
    
        result, error = fetch_data(query, ['id'], params)
        if error:
            logging.error(f"Database error during playerMatch insert/update: {error}")
            execute_query("ROLLBACK;")
            f.abort(500, description="Internal Server Error")

        player_match_id = result[0]['id'] if result else None
        if not player_match_id:
            logging.error(f"Failed to retrieve playerMatch ID after insert/update for player ID {ubisoft_id}")
            execute_query("ROLLBACK;")
            f.abort(500, description="Internal Server Error")
    # endregion

    # region Save Events
    for event in data["events_data"]:
        query = """
        INSERT INTO events (round_id, player_id, target_player_id, type, phase, time_elapsed_seconds,
        operator, refrag, got_refraged, headshot)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id;
        """

        round_number = event["round_number"]
        roundID = rounds_data[round_number - 1]["round.id"]
        player_ubisoft_id = event["player_ubisoft_id"]
        target_ubisoft_id = event["target_player_ubisoft_id"]
        params = (
            roundID,
            data["player_data"][player_ubisoft_id]["player.id"],
            data["player_data"][target_ubisoft_id]["player.id"] if target_ubisoft_id else None,
            event["type"],
            event["phase"],
            event["time_elapsed_seconds"],
            event["operator"],
            event["refrag"],
            event["was_refraged"],
            event["headshot"]
        )

        result, error = fetch_data(query, ['id'], params)
        if error:
            logging.error(f"Database error during events insert/update: {error}")
            execute_query("ROLLBACK;")
            f.abort(500, description="Internal Server Error")

        event_id = result[0]['id'] if result else None
        if not event_id:
            logging.error(f"Failed to retrieve event ID after insert/update for round ID {roundID}")
            execute_query("ROLLBACK;")
            f.abort(500, description="Internal Server Error")
    # endregion

    # Commit if successful
    success, error = execute_query("COMMIT;")
    if error:
        logging.error(f"Database error during initialization [COMMIT]: {error}")
        execute_query("ROLLBACK;")
        f.abort(500, description="Internal Server Error")
    return "Database initialized successfully.", 200

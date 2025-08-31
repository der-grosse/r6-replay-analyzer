##### Datenbank-Abfragen
import re
from numpy import rec
import psycopg2
from vars import DB_LOGIN, PORT, BASE_PATH
import logging
import flask as f

def fetch_data(query, columns, params=None):
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
    
def execute_query(query, params=None):
    """Führt SQL-Befehle aus, die keine Ergebnisse zurückgeben (CREATE, INSERT, UPDATE, DELETE)"""
    try:
        with psycopg2.connect(DB_LOGIN) as con:
            cur = con.cursor()
            cur.execute(query, params)
            con.commit()
            return True, None
    except Exception as e:
        return False, str(e)
    
def save_match(data: dict, team_id: int) -> None:
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
        f.abort(500, description="Internal Server Error")

    if result:  # Wenn Liste nicht leer ist
        logging.info(f"Match {match_id} already exists with ID {result[0]['id']}.")
        data["match_info"]["match.id"] = result[0]['id']
        f.abort(409, description="Conflict: Match already exists.")
    else:  # Wenn Liste leer ist (Match existiert nicht)
        logging.info(f"Match {match_id} does not exist yet.")
    # endregion

    # region Save Player Data
    for ubisoft_id, player_data in data["player_data"].items():
        query = """
            INSERT INTO Player (ubisoft_id, username, timestamp, team_id)
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
            f.abort(500, description="Internal Server Error")
        print(result)
        player_id = result[0]['id'] if result else None
        
        if not player_id:
            logging.error(f"Failed to retrieve player ID after insert/update for Ubisoft ID {player_data.get('ubisoft_id')}")
            f.abort(500, description="Internal Server Error")
        else:
            data["player_data"][ubisoft_id]["player.id"] = player_id
    # endregion

    # region Save Match Data
    match_info = data["match_data"]
    query = """
    INSERT INTO Matches (match_id, player_id, timestamp, game_mode, map, match_type,
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
        f.abort(500, description="Internal Server Error")

    else:
        r_match_id = result[0]['match_id']
        print("Return:", r_match_id)
        print("vorher:", match_info.get("match_id"))

    # endregion
        
    # Commit if successful
    success, error = execute_query("COMMIT;")
    if error:
        logging.error(f"Database error during initialization [COMMIT]: {error}")
        execute_query("ROLLBACK;")
        f.abort(500, description="Internal Server Error")
    return "Database initialized successfully.", 200

import requests as rq
from vars import PORT, BASE_PATH
from db_functions import execute_query
import logging
import flask as f

def initialize_db():
    success, error = execute_query("BEGIN TRANSACTION;")
    if error:
        logging.error(f"Database error during initialization [BEGIN TRANSACTION]: {error}")
        f.abort(500, description="Internal Server Error")
    # Create Player table
    query_player_table = """CREATE TABLE IF NOT EXISTS Player (
                            id SERIAL PRIMARY KEY,
                            ubisoft_id VARCHAR(255),
                            username VARCHAR(255),
                            timestamp TIMESTAMP,
                            team_id INTEGER
                        );"""
    success, error = execute_query(query_player_table)
    if error:
        logging.error(f"Database error during initialization [CREATE TABLE Player]: {error}")
        execute_query("ROLLBACK;")
        f.abort(500, description="Internal Server Error")

    # Create table Matches
    query_matches_table = """CREATE TABLE IF NOT EXISTS Matches (
                             match_id VARCHAR(255) PRIMARY KEY,
                             player_id INTEGER,
                             timestamp TIMESTAMP,
                             game_mode VARCHAR(255),
                             map VARCHAR(255),
                             match_type VARCHAR(255),
                             game_version VARCHAR(255),
                             team_id INTEGER,
                             winner_team_index INTEGER,
                             team0_starting_side VARCHAR(255),
                             FOREIGN KEY (player_id) REFERENCES Player(id)
                        );"""
    success, error = execute_query(query_matches_table)
    if error:
        logging.error(f"Database error during initialization [CREATE TABLE Matches]: {error}")
        execute_query("ROLLBACK;")
        f.abort(500, description="Internal Server Error")
    
    # Create table Rounds
    query_rounds_table = """CREATE TABLE IF NOT EXISTS Rounds (
                            id SERIAL PRIMARY KEY,
                            match_id VARCHAR(255),
                            round_number INTEGER,
                            site VARCHAR(255),
                            winner_team_index INTEGER,
                            time_to_entry INTEGER,
                            atk_team_index INTEGER,
                            def_team_index INTEGER,
                            ok_team_index INTEGER,
                            ok_refrag BOOLEAN,
                            clutch BOOLEAN,
                            win_condition VARCHAR(255),
                            FOREIGN KEY (match_id) REFERENCES Matches(match_id)
                        );"""
    success, error = execute_query(query_rounds_table)
    if error:
        logging.error(f"Database error during initialization [CREATE TABLE Rounds]: {error}")
        execute_query("ROLLBACK;")
        f.abort(500, description="Internal Server Error")
    
    # Create table PlayerRound
    query_player_round_table = """CREATE TABLE IF NOT EXISTS PlayerRound (
                                  id SERIAL PRIMARY KEY,
                                  player_id INTEGER,
                                  round_id INTEGER,
                                  team_index INTEGER,
                                  operator VARCHAR(255),
                                  spawn VARCHAR(255),
                                  kills INTEGER,
                                  death BOOLEAN,
                                  headshots INTEGER,
                                  plant BOOLEAN,
                                  defuse BOOLEAN,
                                  kostpoint BOOLEAN,
                                  oneVx INTEGER,
                                  ok BOOLEAN,
                                  od BOOLEAN,
                                  win BOOLEAN,
                                  atk BOOLEAN,
                                  refrags INTEGER,
                                  got_refraged BOOLEAN,
                                  FOREIGN KEY (player_id) REFERENCES Player(id),
                                  FOREIGN KEY (round_id) REFERENCES Rounds(id)
                              );"""
    success, error = execute_query(query_player_round_table)
    if error:
        logging.error(f"Database error during initialization [CREATE TABLE PlayerRound]: {error}")
        execute_query("ROLLBACK;")
        f.abort(500, description="Internal Server Error")

    # Create PlayerMatch table
    query_player_match_table = """CREATE TABLE IF NOT EXISTS PlayerMatch (
                                  id SERIAL PRIMARY KEY,
                                  player_id INTEGER,
                                  match_id VARCHAR(255),
                                  team_index INTEGER,
                                  kills INTEGER,
                                  assists INTEGER,
                                  deaths INTEGER,
                                  headshots INTEGER,
                                  kost FLOAT,
                                  win BOOLEAN,
                                  won_rounds INTEGER,
                                  lost_rounds INTEGER,
                                  won_atk_rounds INTEGER,
                                  lost_atk_rounds INTEGER,
                                  won_def_rounds INTEGER,
                                  lost_def_rounds INTEGER,
                                  oks INTEGER,
                                  ods INTEGER,
                                  FOREIGN KEY (player_id) REFERENCES Player(id),
                                  FOREIGN KEY (match_id) REFERENCES Matches(match_id)
                              );"""
    success, error = execute_query(query_player_match_table)
    if error:
        logging.error(f"Database error during initialization [CREATE TABLE PlayerMatch]: {error}")
        execute_query("ROLLBACK;")
        f.abort(500, description="Internal Server Error")

    # Create Events table
    query_events_table = """CREATE TABLE IF NOT EXISTS Events (
                            id SERIAL PRIMARY KEY,
                            round_id INTEGER,
                            player_id INTEGER,
                            target_player_id INTEGER,
                            type VARCHAR(255),
                            phase VARCHAR(255),
                            time_elapsed_seconds INTEGER,
                            operator VARCHAR(255),
                            refrag BOOLEAN,
                            got_refragt BOOLEAN,
                            FOREIGN KEY (round_id) REFERENCES Rounds(id),
                            FOREIGN KEY (player_id) REFERENCES Player(id),
                            FOREIGN KEY (target_player_id) REFERENCES Player(id)
                        );"""

    success, error = execute_query(query_events_table)
    if error:
        logging.error(f"Database error during initialization [CREATE TABLE Events]: {error}")
        execute_query("ROLLBACK;")
        f.abort(500, description="Internal Server Error")

    # Commit if successful
    success, error = execute_query("COMMIT;")
    if error:
        logging.error(f"Database error during initialization [COMMIT]: {error}")
        execute_query("ROLLBACK;")
        f.abort(500, description="Internal Server Error")
    return "Database initialized successfully.", 200

if __name__ == "__main__":
    url = f"http://localhost:{PORT}/{BASE_PATH}/initialize"

    response = rq.post(url)
    print(f"Response Status Code: {response.status_code}\nResponse Body: {response.text}\n")
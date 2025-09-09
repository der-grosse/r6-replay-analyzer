import logging

import flask as f
from datetime import datetime as dt
from flask_cors import CORS

from vars import BASE_PATH, MODE, PORT
from auth import get_auth
from db_functions import fetch_data, execute_query, save_match
from initializeDatabase import initialize_db

print("Starting R6 Replay Analyzer API")

app = f.Flask(__name__)

CORS(app) # Script muss nicht auf demselben Server laufen wie API

@app.before_request
def authenticate():
    print(f"Authenticating request to {f.request.path} at {dt.now().isoformat()}")

    if MODE == 'development':
        f.g.user = {'name': 'Elperdano', 'isAdmin': True, 'teamID': 6}
        return
    
    token = f.request.cookies.get('jwt')
    if not token:
        f.abort(401, description="Unauthorized: No token provided")
        
    user = get_auth(token)
    if not user:
        f.abort(401, description="Unauthorized: Invalid token")

    f.g.user = user

@app.route(f'{BASE_PATH}/', methods=['GET'])
def heartbeat():
    return "Authenticated", 200

@app.route(f'{BASE_PATH}/initialize', methods=['POST'])
def initialize():
    message, status_code = initialize_db()
    return message, status_code

@app.route(f'{BASE_PATH}/upload', methods=['POST'])
def upload_replays():
    # TODO: implement
    return "Not implemented", 501

@app.route(f'{BASE_PATH}/upload_json', methods=['POST'])
def upload_json():
    data = f.request.get_json()
    if not data:
        f.abort(400, description="Bad Request: No JSON data provided")

    # Process the JSON data
    save_match(data, f.g.user['teamID'])

    return "JSON data processed successfully", 200

@app.route(f'{BASE_PATH}/get_all_player', methods=['GET'])
def get_all_player() -> dict[list[dict[str, str]]]:
    """
    Gibt alle Spielernamen und Ubisoft IDs zurück, sortiert nach Spielernamen.
    Es wird immer der aktuellste Name zurückgegeben, auch wenn sich der Name geändert hat.
    """

    query = """SELECT p.username as username, p.ubisoft_id as uid
            FROM player p
                INNER JOIN (
                    SELECT ubisoft_id, MAX(timestamp) as max_timestamp
                    FROM player
                    GROUP BY
                        ubisoft_id
                ) sub ON p.ubisoft_id = sub.ubisoft_id
                AND p.timestamp = sub.max_timestamp
            ORDER BY p.username;"""
    data, error = fetch_data(query, ["username","uid"])

    if error:
        print("ERROR")
        f.abort(500, description="Internal Server Error")

    return {"players": data}, 200

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG if MODE == "development" else logging.INFO)
    app.run(port=PORT, debug=(MODE == "development"))
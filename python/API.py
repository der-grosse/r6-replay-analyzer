
import logging

import flask as f
from datetime import datetime as dt
from flask_cors import CORS

from vars import BASE_PATH, MODE, PORT
from auth import get_auth
from db_functions import fetch_data

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

@app.route(f'{BASE_PATH}/upload', methods=['POST'])
def upload_replays():
    # TODO: implement
    return "Not implemented", 501

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG if MODE == "development" else logging.INFO)
    app.run(port=PORT, debug=(MODE == "development"))
import requests as rq
from vars import REQUEST_URL

def get_auth(token) -> dict["teamID": int, "name": str, "isAdmin": bool] | None:
    if not token:
        return None
    response = rq.get(REQUEST_URL, headers={"Authorization": f"Bearer {token}"})
    if response.status_code != 200:
        return None
    return response.json()


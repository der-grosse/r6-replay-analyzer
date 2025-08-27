##### Datenbank-Abfragen
import psycopg2
from vars import DB_LOGIN

def fetch_data(query, columns, params=None):
    try:
        with psycopg2.connect(DB_LOGIN) as con:
            cur = con.cursor()
            cur.execute(query, params)
            rows = cur.fetchall()
            result = [dict(zip(columns, row)) for row in rows]
            return result, None
    except Exception as e:
        return None, str(e)
##### Datenbank-Abfragen
import psycopg2
from vars import DB_LOGIN

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
import os

from dotenv import load_dotenv

load_dotenv(dotenv_path='.env', override=True)  # Lade Umgebungsvariablen aus der .env-Datei

# Connect to the database
DB_LOGIN = f"""host={os.environ.get('DB_HOST')}
                port={os.environ.get('DB_PORT')}
                dbname={os.environ.get('DB_NAME')}
                user={os.environ.get('DB_USER')}
                password={os.environ.get('DB_PSWD')}"""

REQUEST_URL = os.environ.get('AUTH_URL')
BASE_PATH = os.environ.get('BASE_PATH')

if not REQUEST_URL:
    raise ValueError("AUTH_URL is not set in environment variables")
if not BASE_PATH:
    raise ValueError("BASE_PATH is not set in environment variables")
if not os.environ.get('DB_NAME'):
    raise ValueError("DB_NAME is not set in environment variables")
if not os.environ.get('DB_USER'):
    raise ValueError("DB_USER is not set in environment variables")
if not os.environ.get('DB_PSWD'):
    raise ValueError("DB_PSWD is not set in environment variables")
if not os.environ.get('DB_HOST'):
    raise ValueError("DB_HOST is not set in environment variables")
if not os.environ.get('DB_PORT'):
    raise ValueError("DB_PORT is not set in environment variables")
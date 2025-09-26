import os
from dotenv import load_dotenv, find_dotenv
from app import create_app, socketio

# Always load .env regardless of CWD
load_dotenv(find_dotenv())

app = create_app()

if __name__ == '__main__':
    host = os.getenv('FLASK_RUN_HOST', '127.0.0.1')
    port = int(os.getenv('FLASK_RUN_PORT', '5000'))
    socketio.run(app, host=host, port=port)

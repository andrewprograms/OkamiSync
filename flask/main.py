import os
from dotenv import load_dotenv, find_dotenv
from app import create_app, socketio

load_dotenv(find_dotenv())

app = create_app()

if __name__ == '__main__':
    host = os.getenv('FLASK_RUN_HOST', '127.0.0.1')
    port = int(os.getenv('FLASK_RUN_PORT', '5000'))
    # eventlet is installed; this will serve WebSockets
    socketio.run(app, host=host, port=port)

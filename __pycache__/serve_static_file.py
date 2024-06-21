import os
from flask import Flask, send_from_directory

app = Flask(__name__)

@app.route('/static/<path:filename>')
def serve_static(filename):
    directory = os.path.join(os.getcwd(), 'static')
    return send_from_directory(directory, filename)

if __name__ == "__main__":
    app.run(port=8501)
from flask import Flask
from route import data

app = Flask(__name__)
app.register_blueprint(data, url_prefix='/')

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)

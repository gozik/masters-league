from flask import Flask, render_template
from flask_bootstrap import Bootstrap

app = Flask(__name__)
Bootstrap(app)

# Sample data - replace with your actual data source
players = [
    {"rank": 1, "name": "Novak Djokovic", "rating": 9850, "country": "SRB", "age": 34},
    {"rank": 2, "name": "Daniil Medvedev", "rating": 8930, "country": "RUS", "age": 25},
    {"rank": 3, "name": "Rafael Nadal", "rating": 8425, "country": "ESP", "age": 35},
    {"rank": 4, "name": "Stefanos Tsitsipas", "rating": 7980, "country": "GRE", "age": 23},
    {"rank": 5, "name": "Alexander Zverev", "rating": 7865, "country": "GER", "age": 24},
]


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/ratings')
def show_ratings():
    return render_template('ratings.html', players=players)


if __name__ == '__main__':
    app.run(debug=True)

from flask import Flask, request, render_template_string
import sqlite3

app = Flask(__name__)

def get_db():
    conn = sqlite3.connect('names.db')
    return conn

@app.route('/', methods=['GET', 'POST'])
def index():
    greeting = None
    if request.method == 'POST':
        name = request.form['name']
        conn = get_db()
        c = conn.cursor()
        c.execute('INSERT INTO names (name) VALUES (?)', (name,))
        conn.commit()
        conn.close()
        greeting = f"Hello, {name}!"
    return render_template_string('''
        <form method="post">
            Name: <input type="text" name="name">
            <input type="submit" value="Submit">
        </form>
        {% if greeting %}<h2>{{ greeting }}</h2>{% endif %}
    ''', greeting=greeting)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

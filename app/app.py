from flask import Flask, request, render_template_string, jsonify
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

@app.route('/healthz')
def healthz():
    try:
        conn = get_db()
        conn.execute('SELECT 1')
        conn.close()
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        return jsonify({"status": "error", "detail": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

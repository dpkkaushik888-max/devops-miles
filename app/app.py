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
        <!DOCTYPE html>
        <html>
        <head>
            <title>Names App</title>
            <style>
                body {
                    margin: 0;
                    padding: 0;
                    min-height: 100vh;
                    background: url('https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=1920&q=80') no-repeat center center fixed;
                    background-size: cover;
                    font-family: Arial, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                }
                .container {
                    background: rgba(255, 255, 255, 0.85);
                    padding: 40px;
                    border-radius: 12px;
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
                    text-align: center;
                    max-width: 400px;
                    width: 90%;
                }
                h1 { color: #333; margin-bottom: 20px; }
                h2 { color: #2e7d32; }
                input[type="text"] {
                    padding: 10px;
                    font-size: 16px;
                    border: 2px solid #ccc;
                    border-radius: 6px;
                    width: 200px;
                    margin-right: 10px;
                }
                input[type="submit"] {
                    padding: 10px 20px;
                    font-size: 16px;
                    background: #2e7d32;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    cursor: pointer;
                }
                input[type="submit"]:hover { background: #1b5e20; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Welcome</h1>
                <form method="post">
                    <input type="text" name="name" placeholder="Enter your name">
                    <input type="submit" value="Submit">
                </form>
                {% if greeting %}<h2>{{ greeting }}</h2>{% endif %}
            </div>
        </body>
        </html>
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

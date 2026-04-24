import sqlite3
from dotenv import load_dotenv
from os import getenv
from authlib.integrations.flask_client import OAuth
from flask import Flask, redirect, url_for, session, render_template

load_dotenv()

app = Flask(__name__)
app.secret_key = getenv("SECRET_KEY")

oauth = OAuth(app)

google = oauth.register(
        name="google",
        client_id=getenv("GOOGLE_CLIENT_ID"),
        client_secret=getenv("GOOGLE_CLIENT_SECRET"),
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={
            "scope": "openid email profile"
            }
)
def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        google_id TEXT,
        name TEXT,
        email TEXT,
        picture TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()
@app.route('/')
def i():
    return redirect(url_for('home'))

@app.route('/home')
def home():
    if "user" in session:
        name = session["user"]["given_name"] or session["user"]["name"]
        picture = session["user"]["picture"]
        return render_template("index.html", user=name, picture=picture)
    return redirect(url_for('login'))

@app.route('/login')
def login():
    return google.authorize_redirect(url_for('callback', _external=True))

@app.route('/callback')
def callback():
    token = google.authorize_access_token()
    user = google.get("https://openidconnect.googleapis.com/v1/userinfo").json()

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM users WHERE google_id = ?", (user["sub"],))
    find = cursor.fetchone()
    if not find:
        session["user_id"] = cursor.lastrowid
        cursor.execute("INSERT INTO users (google_id, name, picture, email) VALUES (?, ?, ?, ?) RETURNING id", (user.get("sub"), user.get("given_name") or user.get("name"), user.get("picture"), user.get("email")))
        user_id = cursor.fetchone()[0]
    else:
        user_id = find[0]
    conn.commit()
    conn.close()
    session["user_id"] = user_id
    session["user"] = user
    return redirect(url_for("home"))
if __name__ == "__main__":
        port = getenv("PORT")
        app.run(host="0.0.0.0", port=port)


import sqlite3
import datetime
from functools import wraps

import jwt
from flask import Flask, request, jsonify

app = Flask(__name__)

# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

SECRET_KEY = "gezondheidscoach_secret_key_2026_secure"
DATABASE = "healthcoach.db"

# Demo account for the assignment
users = {
    "chenine bipat": "12345"
}


# --------------------------------------------------
# DATABASE
# --------------------------------------------------

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS health_records (
            username TEXT PRIMARY KEY,
            sleep TEXT NOT NULL,
            exercise TEXT NOT NULL,
            nutrition TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS health_goals (
            username TEXT PRIMARY KEY,
            sleep_goal REAL NOT NULL,
            exercise_goal REAL NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# --------------------------------------------------
# HELPER FUNCTIONS
# --------------------------------------------------

def create_token(username, token_type, duration):
    payload = {
        "username": username,
        "token_type": token_type,
        "exp": datetime.datetime.now(datetime.timezone.utc) + duration
    }

    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


def get_authenticated_user():
    auth_header = request.headers.get("Authorization", "")

    if not auth_header.startswith("Bearer "):
        return None, (jsonify({"error": "Token ontbreekt"}), 401)

    token = auth_header.split(" ", 1)[1].strip()

    try:
        decoded = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=["HS256"]
        )

        if decoded.get("token_type") != "access":
            return None, (jsonify({"error": "Ongeldig access token"}), 403)

        username = decoded.get("username")

        if username not in users:
            return None, (jsonify({"error": "Gebruiker niet gevonden"}), 401)

        return username, None

    except jwt.ExpiredSignatureError:
        return None, (jsonify({"error": "Token verlopen"}), 401)

    except jwt.InvalidTokenError:
        return None, (jsonify({"error": "Ongeldig token"}), 401)


def get_number(value):
    """Extract a positive numeric value from health data."""
    try:
        number = float(
            str(value).lower()
            .replace("hours", "")
            .replace("hour", "")
            .replace("minutes", "")
            .replace("minute", "")
            .strip()
        )

        if number < 0:
            return None

        return number

    except (ValueError, TypeError):
        return None


# --------------------------------------------------
# HOME
# --------------------------------------------------

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "Welkom bij de Gezondheidscoach API!",
        "endpoints": [
            "/login",
            "/refresh",
            "/upload",
            "/analyse",
            "/tips",
            "/goals",
            "/progress"
        ]
    }), 200


# --------------------------------------------------
# LOGIN
# --------------------------------------------------

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Ongeldige JSON"}), 400

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Gebruikersnaam en wachtwoord verplicht"}), 400

    username = str(username).strip().lower()

    if users.get(username) != password:
        return jsonify({"error": "Ongeldige inloggegevens"}), 401

    access_token = create_token(
        username,
        "access",
        datetime.timedelta(hours=1)
    )

    refresh_token = create_token(
        username,
        "refresh",
        datetime.timedelta(days=7)
    )

    return jsonify({
        "message": "Login succesvol!",
        "token": access_token,
        "refresh_token": refresh_token
    }), 200


# --------------------------------------------------
# REFRESH TOKEN
# --------------------------------------------------

@app.route("/refresh", methods=["POST"])
def refresh():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Ongeldige JSON"}), 400

    refresh_token = data.get("refresh_token")

    if not refresh_token:
        return jsonify({"error": "Refresh token ontbreekt"}), 401

    try:
        decoded = jwt.decode(
            refresh_token,
            SECRET_KEY,
            algorithms=["HS256"]
        )

        if decoded.get("token_type") != "refresh":
            return jsonify({"error": "Ongeldig refresh token"}), 403

        username = decoded.get("username")

        if username not in users:
            return jsonify({"error": "Gebruiker niet gevonden"}), 401

        new_token = create_token(
            username,
            "access",
            datetime.timedelta(hours=1)
        )

        return jsonify({
            "message": "Token succesvol vernieuwd!",
            "token": new_token
        }), 200

    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Refresh token verlopen"}), 401

    except jwt.InvalidTokenError:
        return jsonify({"error": "Ongeldig refresh token"}), 401


# --------------------------------------------------
# UPLOAD HEALTH DATA
# --------------------------------------------------

@app.route("/upload", methods=["POST"])
def upload():
    username, error = get_authenticated_user()

    if error:
        return error

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Ongeldige JSON"}), 400

    required_fields = ["sleep", "exercise", "nutrition"]

    if any(
        field not in data or data[field] is None or str(data[field]).strip() == ""
        for field in required_fields
    ):
        return jsonify({"error": "Alle gezondheidsgegevens zijn verplicht"}), 400

    if get_number(data["sleep"]) is None or get_number(data["exercise"]) is None:
        return jsonify({"error": "Ongeldige slaap- of bewegingsgegevens"}), 400

    conn = get_db_connection()

    conn.execute("""
        INSERT OR REPLACE INTO health_records
        (username, sleep, exercise, nutrition)
        VALUES (?, ?, ?, ?)
    """, (
        username,
        str(data["sleep"]),
        str(data["exercise"]),
        str(data["nutrition"])
    ))

    conn.commit()
    conn.close()

    return jsonify({
        "message": "Gezondheidsgegevens succesvol opgeslagen!",
        "user": username,
        "data": data
    }), 200


# --------------------------------------------------
# ANALYSE HEALTH DATA
# --------------------------------------------------

@app.route("/analyse", methods=["GET"])
def analyse():
    username, error = get_authenticated_user()

    if error:
        return error

    conn = get_db_connection()

    record = conn.execute("""
        SELECT sleep, exercise, nutrition
        FROM health_records
        WHERE username = ?
    """, (username,)).fetchone()

    conn.close()

    if record is None:
        return jsonify({"error": "Geen gezondheidsgegevens gevonden"}), 404

    sleep_hours = get_number(record["sleep"])
    exercise_minutes = get_number(record["exercise"])

    if sleep_hours is None or exercise_minutes is None:
        return jsonify({"error": "Ongeldige gezondheidsgegevens"}), 400

    insights = []

    if sleep_hours < 7:
        insights.append("Je slaapt mogelijk te weinig.")
    elif sleep_hours <= 9:
        insights.append("Je slaapduur ziet er goed uit.")
    else:
        insights.append("Je slaapt langer dan 9 uur.")

    if exercise_minutes < 30:
        insights.append("Probeer meer dagelijks te bewegen.")
    else:
        insights.append("Goed bezig met je dagelijkse beweging!")

    return jsonify({
        "message": "Gezondheidsanalyse succesvol uitgevoerd!",
        "user": username,
        "analysis": {
            "sleep_hours": sleep_hours,
            "exercise_minutes": exercise_minutes,
            "nutrition": record["nutrition"],
            "insights": insights
        }
    }), 200


# --------------------------------------------------
# HEALTH RECOMMENDATIONS
# --------------------------------------------------

@app.route("/tips", methods=["GET"])
def tips():
    username, error = get_authenticated_user()

    if error:
        return error

    conn = get_db_connection()

    record = conn.execute("""
        SELECT sleep, exercise, nutrition
        FROM health_records
        WHERE username = ?
    """, (username,)).fetchone()

    conn.close()

    if record is None:
        return jsonify({"error": "Geen gezondheidsgegevens gevonden"}), 404

    sleep_hours = get_number(record["sleep"])
    exercise_minutes = get_number(record["exercise"])

    if sleep_hours is None or exercise_minutes is None:
        return jsonify({"error": "Ongeldige gezondheidsgegevens"}), 400

    recommendations = []

    if sleep_hours < 7:
        recommendations.append("Probeer regelmatig 7 tot 9 uur te slapen.")

    if exercise_minutes < 30:
        recommendations.append("Probeer dagelijks meer te bewegen.")

    if record["nutrition"].lower() not in ["healthy", "gezond"]:
        recommendations.append("Kies vaker voor gezonde en gevarieerde voeding.")

    if not recommendations:
        recommendations.append("Blijf gezond en gevarieerd eten.")
        recommendations.append("Blijf voldoende bewegen en goed slapen.")

    return jsonify({
        "message": "Gezondheidsaanbevelingen succesvol gegenereerd!",
        "user": username,
        "recommendations": recommendations
    }), 200


# --------------------------------------------------
# SET PERSONAL HEALTH GOALS
# --------------------------------------------------

@app.route("/goals", methods=["POST"])
def set_goals():
    username, error = get_authenticated_user()

    if error:
        return error

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Ongeldige JSON"}), 400

    sleep_goal = get_number(data.get("sleep_goal"))
    exercise_goal = get_number(data.get("exercise_goal"))

    if (
        sleep_goal is None or exercise_goal is None
        or sleep_goal <= 0 or exercise_goal <= 0
    ):
        return jsonify({
            "error": "Doelen moeten positieve getallen zijn."
        }), 400

    conn = get_db_connection()

    conn.execute("""
        INSERT OR REPLACE INTO health_goals
        (username, sleep_goal, exercise_goal)
        VALUES (?, ?, ?)
    """, (username, sleep_goal, exercise_goal))

    conn.commit()
    conn.close()

    return jsonify({
        "message": "Gezondheidsdoelen succesvol opgeslagen!",
        "user": username,
        "goals": {
            "sleep_goal": sleep_goal,
            "exercise_goal": exercise_goal
        }
    }), 200


# --------------------------------------------------
# TRACK PERSONAL PROGRESS
# --------------------------------------------------

@app.route("/progress", methods=["GET"])
def progress():
    username, error = get_authenticated_user()

    if error:
        return error

    conn = get_db_connection()

    goals = conn.execute("""
        SELECT sleep_goal, exercise_goal
        FROM health_goals
        WHERE username = ?
    """, (username,)).fetchone()

    record = conn.execute("""
        SELECT sleep, exercise
        FROM health_records
        WHERE username = ?
    """, (username,)).fetchone()

    conn.close()

    if goals is None:
        return jsonify({
            "error": "Geen gezondheidsdoelen gevonden. Stel eerst doelen in."
        }), 404

    if record is None:
        return jsonify({
            "error": "Geen gezondheidsgegevens gevonden. Upload eerst gegevens."
        }), 404

    sleep_hours = get_number(record["sleep"])
    exercise_minutes = get_number(record["exercise"])

    if sleep_hours is None or exercise_minutes is None:
        return jsonify({"error": "Ongeldige gezondheidsgegevens"}), 400

    return jsonify({
        "message": "Voortgang succesvol berekend!",
        "user": username,
        "progress": {
            "sleep": {
                "goal": goals["sleep_goal"],
                "actual": sleep_hours,
                "achieved": sleep_hours >= goals["sleep_goal"]
            },
            "exercise": {
                "goal": goals["exercise_goal"],
                "actual": exercise_minutes,
                "achieved": exercise_minutes >= goals["exercise_goal"]
            }
        }
    }), 200


# --------------------------------------------------
# START APPLICATION
# --------------------------------------------------

if __name__ == "__main__":
    init_db()
    app.run(debug=True)

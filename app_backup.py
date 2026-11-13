
from flask import Flask, jsonify, request
import jwt
import datetime

# =====================================
# 1. INITIALIZE FLASK APPLICATION
# =====================================

app = Flask(__name__)

SECRET_KEY = "gezondheidscoach_secret_key_2026_secure"

users = {
    "chenine bipat": "12345"
}

# Temporary storage for health data
health_records = {}
health_goals = {}


# =====================================
# 2. HELPER: VERIFY ACCESS TOKEN
# =====================================

def get_authenticated_user():

    auth_header = request.headers.get("Authorization", "")

    if not auth_header.startswith("Bearer "):
        return None, (jsonify({
            "error": "Token ontbreekt"
        }), 401)

    token = auth_header.split(" ", 1)[1].strip()

    try:
        decoded_token = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=["HS256"]
        )

        if decoded_token.get("token_type") != "access":
            return None, (jsonify({
                "error": "Ongeldig access token"
            }), 401)

        username = decoded_token.get("username")

        if username not in users:
            return None, (jsonify({
                "error": "Gebruiker niet gevonden"
            }), 401)

        return username, None

    except jwt.ExpiredSignatureError:
        return None, (jsonify({
            "error": "Token verlopen"
        }), 401)

    except jwt.InvalidTokenError:
        return None, (jsonify({
            "error": "Ongeldig token"
        }), 401)


# =====================================
# 3. HOME ENDPOINT
# =====================================

@app.route("/", methods=["GET"])
def home():

    return jsonify({
        "message": "Welkom bij de Gezondheidscoach API!",
        "status": "API is actief"
    }), 200


# =====================================
# 4. LOGIN ENDPOINT
# =====================================

@app.route("/login", methods=["POST"])
def login():

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "error": "Ongeldige JSON"
        }), 400

    username = data.get("username")
    password = data.get("password")

    if username in users and users[username] == password:

        access_token = jwt.encode(
            {
                "username": username,
                "token_type": "access",
                "exp": datetime.datetime.now(datetime.timezone.utc)
                + datetime.timedelta(hours=1)
            },
            SECRET_KEY,
            algorithm="HS256"
        )

        refresh_token = jwt.encode(
            {
                "username": username,
                "token_type": "refresh",
                "exp": datetime.datetime.now(datetime.timezone.utc)
                + datetime.timedelta(days=7)
            },
            SECRET_KEY,
            algorithm="HS256"
        )

        return jsonify({
            "message": "Login succesvol!",
            "token": access_token,
            "refresh_token": refresh_token
        }), 200

    return jsonify({
        "error": "Ongeldige gebruikersnaam of wachtwoord"
    }), 401


# =====================================
# 5. TOKEN RENEWAL ENDPOINT
# =====================================

@app.route("/refresh", methods=["POST"])
def refresh():

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "error": "Ongeldige JSON"
        }), 400

    refresh_token = data.get("refresh_token")

    if not refresh_token:
        return jsonify({
            "error": "Refresh token ontbreekt"
        }), 401

    try:
        decoded = jwt.decode(
            refresh_token,
            SECRET_KEY,
            algorithms=["HS256"]
        )

        if decoded.get("token_type") != "refresh":
            return jsonify({
                "error": "Ongeldig refresh token"
            }), 401

        username = decoded.get("username")

        if username not in users:
            return jsonify({
                "error": "Gebruiker niet gevonden"
            }), 401

        new_access_token = jwt.encode(
            {
                "username": username,
                "token_type": "access",
                "exp": datetime.datetime.now(datetime.timezone.utc)
                + datetime.timedelta(hours=1)
            },
            SECRET_KEY,
            algorithm="HS256"
        )

        return jsonify({
            "message": "Token succesvol vernieuwd!",
            "token": new_access_token
        }), 200

    except jwt.ExpiredSignatureError:
        return jsonify({
            "error": "Refresh token verlopen"
        }), 401

    except jwt.InvalidTokenError:
        return jsonify({
            "error": "Ongeldig refresh token"
        }), 401


# =====================================
# 6. UPLOAD HEALTH DATA ENDPOINT
# =====================================

@app.route("/upload", methods=["POST"])
def upload():

    username, error = get_authenticated_user()

    if error:
        return error

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "error": "Ongeldige JSON"
        }), 400

    health_records[username] = data

    return jsonify({
        "message": "Gezondheidsgegevens succesvol opgeslagen!",
        "user": username,
        "health_data": health_records[username]
    }), 200



# =====================================
# PERSONAL HEALTH GOALS ENDPOINT
# =====================================

@app.route("/goals", methods=["POST"])
def set_goals():

    username, error = get_authenticated_user()

    if error:
        return error

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "error": "Ongeldige JSON"
        }), 400

    sleep_goal = data.get("sleep_goal")
    exercise_goal = data.get("exercise_goal")

    try:
        sleep_goal = float(sleep_goal)
        exercise_goal = float(exercise_goal)

        if sleep_goal <= 0 or exercise_goal <= 0:
            raise ValueError

    except (ValueError, TypeError):
        return jsonify({
            "error": "Doelen moeten positieve getallen zijn."
        }), 400

    health_goals[username] = {
        "sleep_goal": sleep_goal,
        "exercise_goal": exercise_goal
    }

    return jsonify({
        "message": "Gezondheidsdoelen succesvol opgeslagen!",
        "user": username,
        "goals": health_goals[username]
    }), 200



# =====================================
# HEALTH PROGRESS TRACKING ENDPOINT
# =====================================

@app.route("/progress", methods=["GET"])
def progress():

    username, error = get_authenticated_user()

    if error:
        return error

    if username not in health_goals:
        return jsonify({
            "error": "Geen gezondheidsdoelen gevonden. Stel eerst doelen in."
        }), 404

    if username not in health_records:
        return jsonify({
            "error": "Geen gezondheidsgegevens gevonden. Upload eerst gegevens."
        }), 404

    data = health_records[username]
    goals = health_goals[username]

    try:
        sleep_hours = float(
            str(data.get("sleep", ""))
            .lower()
            .replace("hours", "")
            .replace("hour", "")
            .strip()
        )

        exercise_minutes = float(
            str(data.get("exercise", ""))
            .lower()
            .replace("minutes", "")
            .replace("minute", "")
            .strip()
        )

    except (ValueError, TypeError):
        return jsonify({
            "error": "Ongeldige gezondheidsgegevens."
        }), 400

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



# =====================================
# 7. HEALTH ANALYSIS ENDPOINT
# =====================================

@app.route("/analyse", methods=["GET"])
def analyse():

    username, error = get_authenticated_user()

    if error:
        return error

    if username not in health_records:
        return jsonify({
            "error": "Geen gezondheidsgegevens gevonden"
        }), 404

    data = health_records[username]

    # Analyze sleep
    try:
        sleep_hours = float(
            str(data.get("sleep", ""))
            .lower()
            .replace("hours", "")
            .replace("hour", "")
            .strip()
        )
    except (ValueError, TypeError):
        return jsonify({
            "error": "Sleep must be entered as a number of hours"
        }), 400

    # Analyze exercise
    try:
        exercise_minutes = float(
            str(data.get("exercise", ""))
            .lower()
            .replace("minutes", "")
            .replace("minute", "")
            .strip()
        )
    except (ValueError, TypeError):
        return jsonify({
            "error": "Exercise must be entered as a number of minutes"
        }), 400

    insights = []

    if sleep_hours < 7:
        insights.append(
            "Je slaapt mogelijk te weinig. Probeer voldoende rust te nemen."
        )
    else:
        insights.append(
            "Je slaapduur ziet er goed uit."
        )

    if exercise_minutes < 30:
        insights.append(
            "Probeer meer dagelijkse beweging toe te voegen."
        )
    else:
        insights.append(
            "Goed bezig met je dagelijkse beweging!"
        )

    return jsonify({
        "message": "Gezondheidsanalyse succesvol uitgevoerd!",
        "user": username,
        "sleep_hours": sleep_hours,
        "exercise_minutes": exercise_minutes,
        "nutrition": data.get("nutrition", "Niet opgegeven"),
        "insights": insights
    }), 200


# =====================================
# 8. HEALTH RECOMMENDATIONS ENDPOINT
# =====================================

@app.route("/tips", methods=["GET"])
def tips():

    username, error = get_authenticated_user()

    if error:
        return error

    if username not in health_records:
        return jsonify({
            "error": "Geen gezondheidsgegevens gevonden"
        }), 404

    data = health_records[username]

    tips_list = []

    sleep = str(data.get("sleep", "")).lower()
    exercise = str(data.get("exercise", "")).lower()

    if "8" not in sleep and "9" not in sleep and "10" not in sleep:
        tips_list.append(
            "Probeer elke nacht voldoende te slapen."
        )

    if "30" not in exercise and "45" not in exercise and "60" not in exercise:
        tips_list.append(
            "Probeer dagelijks minstens 30 minuten te bewegen."
        )

    tips_list.append(
        "Blijf gezond en gevarieerd eten."
    )

    tips_list.append(
        "Drink voldoende water gedurende de dag."
    )

    return jsonify({
        "message": "Gezondheidsaanbevelingen succesvol gegenereerd!",
        "user": username,
        "recommendations": tips_list
    }), 200


# =====================================
# 9. RUN APPLICATION
# =====================================

if __name__ == "__main__":
    app.run(debug=True)

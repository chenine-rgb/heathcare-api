
from flask import Flask, render_template_string
import sqlite3
import os

app = Flask(__name__)

# DATABASE CONFIGURATION
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "healthcoach.db")


# CONVERT DATABASE VALUES INTO NUMBERS
def extract_number(value):
    if isinstance(value, (int, float)):
        return float(value)

    return float(str(value).strip().split()[0])


# DASHBOARD DESIGN
HTML = """
<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <title>Gezondheidscoach | Health Dashboard</title>

    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

    <style>
        :root {
            --pink: #D96C9D;
            --rose: #E9A3C1;
            --blush: #F7DCE7;
            --dark: #38343A;
            --grey: #85818A;
            --light-grey: #E6E5E8;
            --background: #F8F5F7;
            --white: #FFFFFF;
        }

        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            padding: 35px;
            font-family: Arial, sans-serif;
            background: var(--background);
            color: var(--dark);
        }

        .container {
            max-width: 1250px;
            margin: auto;
        }

        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 35px;
        }

        .header h1 {
            margin: 0;
            font-size: 30px;
            letter-spacing: -1px;
        }

        .header p {
            color: var(--grey);
            font-size: 13px;
            letter-spacing: 1.5px;
        }

        .header-icon {
            background: var(--blush);
            color: var(--pink);
            padding: 15px;
            border-radius: 14px;
            font-size: 27px;
        }

        .section-title {
            font-size: 17px;
            margin-bottom: 18px;
        }

        .cards {
            display: grid;
            grid-template-columns:
                repeat(auto-fit, minmax(220px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .card {
            background: var(--white);
            padding: 25px;
            border-radius: 17px;
            box-shadow: 0 5px 20px rgba(56, 52, 58, 0.045);
            border: 1px solid #F0EAF0;
        }

        .card-top {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .card-icon {
            width: 45px;
            height: 45px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 13px;
            font-size: 23px;
        }

        .pink-icon {
            background: var(--blush);
            color: var(--pink);
        }

        .rose-icon {
            background: #F2C9DA;
            color: #A84973;
        }

        .grey-icon {
            background: var(--light-grey);
            color: var(--dark);
        }

        .card h3 {
            font-size: 14px;
            color: var(--grey);
            font-weight: 500;
            margin: 20px 0 8px;
        }

        .value {
            font-size: 30px;
            font-weight: bold;
            color: var(--dark);
        }

        .goal {
            color: var(--grey);
            font-size: 13px;
            margin-top: 8px;
        }

        .chart-grid {
            display: grid;
            grid-template-columns:
                repeat(auto-fit, minmax(320px, 1fr));
            gap: 20px;
        }

        .chart-card {
            background: var(--white);
            padding: 25px;
            border-radius: 17px;
            box-shadow: 0 5px 20px rgba(56, 52, 58, 0.045);
            border: 1px solid #F0EAF0;
        }

        .chart-card h3 {
            font-size: 16px;
            margin: 0 0 7px;
        }

        .chart-card p {
            color: var(--grey);
            font-size: 12px;
            margin-bottom: 22px;
        }

        .chart-wrapper {
            position: relative;
            height: 260px;
        }

        .footer {
            text-align: center;
            color: var(--grey);
            font-size: 12px;
            margin-top: 35px;
        }

        @media (max-width: 600px) {
            body {
                padding: 18px;
            }

            .header h1 {
                font-size: 23px;
            }
        }
    </style>
</head>

<body>

<div class="container">

    <div class="header">
        <div>
            <h1>Health Overview</h1>
            <p>PERSONAL HEALTH MONITORING</p>
        </div>

        <div class="header-icon">♡</div>
    </div>

    <h2 class="section-title">Health Summary</h2>

    <div class="cards">

        <div class="card">
            <div class="card-top">
                <div class="card-icon pink-icon">☾</div>
            </div>

            <h3>Sleep Duration</h3>
            <div class="value">{{ sleep }} h</div>

            <div class="goal">
                Daily goal: {{ sleep_goal }} hours
            </div>
        </div>

        <div class="card">
            <div class="card-top">
                <div class="card-icon rose-icon">♡</div>
            </div>

            <h3>Physical Activity</h3>
            <div class="value">{{ exercise }} min</div>

            <div class="goal">
                Daily goal: {{ exercise_goal }} minutes
            </div>
        </div>

        <div class="card">
            <div class="card-top">
                <div class="card-icon grey-icon">✧</div>
            </div>

            <h3>Nutrition</h3>

            <div class="value" style="font-size: 23px;">
                {{ nutrition }}
            </div>

            <div class="goal">Nutrition overview</div>
        </div>

    </div>

    <h2 class="section-title">Health Analytics</h2>

    <div class="chart-grid">

        <div class="chart-card">
            <h3>Sleep Analysis</h3>
            <p>Actual sleep compared with your daily goal</p>

            <div class="chart-wrapper">
                <canvas id="sleepChart"></canvas>
            </div>
        </div>

        <div class="chart-card">
            <h3>Physical Activity</h3>
            <p>Actual exercise compared with your daily goal</p>

            <div class="chart-wrapper">
                <canvas id="exerciseChart"></canvas>
            </div>
        </div>

        <div class="chart-card">
            <h3>Goal Achievement</h3>
            <p>Percentage of personal health goals reached</p>

            <div class="chart-wrapper">
                <canvas id="progressChart"></canvas>
            </div>
        </div>

    </div>

    <div class="footer">
        Gezondheidscoach API · Personal Health Monitoring System
    </div>

</div>

<script>

const sleep = {{ sleep | tojson }};
const sleepGoal = {{ sleep_goal | tojson }};
const exercise = {{ exercise | tojson }};
const exerciseGoal = {{ exercise_goal | tojson }};

const pink = '#D96C9D';
const rose = '#E9A3C1';
const blush = '#F7DCE7';
const darkGrey = '#38343A';
const mediumGrey = '#85818A';
const lightGrey = '#E6E5E8';

Chart.defaults.font.family = 'Arial';
Chart.defaults.color = mediumGrey;


// SLEEP CHART
new Chart(document.getElementById('sleepChart'), {
    type: 'bar',

    data: {
        labels: ['Actual', 'Goal'],

        datasets: [{
            label: 'Sleep hours',
            data: [sleep, sleepGoal],

            backgroundColor: [pink, blush],
            borderRadius: 8,
            barThickness: 45
        }]
    },

    options: {
        responsive: true,
        maintainAspectRatio: false,

        plugins: {
            legend: {
                display: false
            }
        },

        scales: {
            y: {
                beginAtZero: true,
                grid: {
                    color: '#F0EDF0'
                }
            },

            x: {
                grid: {
                    display: false
                }
            }
        }
    }
});


// EXERCISE CHART
new Chart(document.getElementById('exerciseChart'), {
    type: 'bar',

    data: {
        labels: ['Actual', 'Goal'],

        datasets: [{
            label: 'Exercise minutes',
            data: [exercise, exerciseGoal],

            backgroundColor: [rose, lightGrey],
            borderRadius: 8,
            barThickness: 45
        }]
    },

    options: {
        responsive: true,
        maintainAspectRatio: false,

        plugins: {
            legend: {
                display: false
            }
        },

        scales: {
            y: {
                beginAtZero: true,
                grid: {
                    color: '#F0EDF0'
                }
            },

            x: {
                grid: {
                    display: false
                }
            }
        }
    }
});


// HEALTH GOAL PROGRESS CHART
new Chart(document.getElementById('progressChart'), {
    type: 'bar',

    data: {
        labels: ['Sleep', 'Exercise'],

        datasets: [{
            label: 'Goal achieved (%)',

            data: [
                sleepGoal > 0
                    ? Math.min(sleep / sleepGoal * 100, 100)
                    : 0,

                exerciseGoal > 0
                    ? Math.min(exercise / exerciseGoal * 100, 100)
                    : 0
            ],

            backgroundColor: [pink, rose],
            borderRadius: 8,
            barThickness: 45
        }]
    },

    options: {
        responsive: true,
        maintainAspectRatio: false,

        plugins: {
            legend: {
                display: false
            }
        },

        scales: {
            y: {
                beginAtZero: true,
                max: 100,

                grid: {
                    color: '#F0EDF0'
                }
            },

            x: {
                grid: {
                    display: false
                }
            }
        }
    }
});

</script>

</body>
</html>
"""


# DASHBOARD ROUTE
@app.route("/")
def dashboard():

    if not os.path.exists(DATABASE):
        return "Database niet gevonden: " + DATABASE, 404

    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row

    try:
        record = connection.execute(
            "SELECT * FROM health_records LIMIT 1"
        ).fetchone()

        goal = connection.execute(
            "SELECT * FROM health_goals LIMIT 1"
        ).fetchone()

    finally:
        connection.close()

    if record is None or goal is None:
        return "Geen gezondheidsgegevens of doelen gevonden.", 404

    # READ HEALTH DATA
    sleep = extract_number(record["sleep"])
    exercise = extract_number(record["exercise"])
    nutrition = str(record["nutrition"])

    # READ PERSONAL GOALS
    sleep_goal = extract_number(goal["sleep_goal"])
    exercise_goal = extract_number(goal["exercise_goal"])

    # DISPLAY DASHBOARD
    return render_template_string(
        HTML,
        sleep=sleep,
        exercise=exercise,
        nutrition=nutrition,
        sleep_goal=sleep_goal,
        exercise_goal=exercise_goal
    )


# START APPLICATION
if __name__ == "__main__":
    app.run(port=5001, debug=True)

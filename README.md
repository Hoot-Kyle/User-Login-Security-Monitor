# User Login Security Monitor

A SOC-style dashboard, built with Python and Streamlit, that watches a live stream of login events and flags the risky ones in real time. It's a from-scratch simulation of the kind of login-monitoring view a security analyst would use to spot suspicious sign-in activity — failed logins, after-hours access, sign-ins from high-risk countries, and unrecognized devices.

## Overview

The project is split into two independent pieces that mirror how a real detection pipeline works:

- **`login_generator.py`** — a producer script that continuously creates realistic, randomized login events (using [Faker](https://faker.readthedocs.io/)) and writes them to a shared SQLite database.
- **`login_check.py`** — the Streamlit dashboard, which polls that database for new events, scores each one against a set of detection rules, and surfaces alerts as they happen.

Because the two run as separate processes talking through a database, the dashboard behaves like a real live feed rather than replaying a static, pre-loaded file.

## Features

- **Live event stream** — new logins appear on the dashboard as the generator writes them, no manual refresh needed
- **Risk-based alerting** — every login is scored and color-coded by severity (green/yellow/red)
- **KPI overview** — total logins, events processed, active alerts, and high-risk alert counts at a glance
- **Login volume chart** — a bar chart of total logins vs. alerts by hour of day
- **Alert filtering** — filter the alert feed by severity tier or by user
- **Playback controls** — start, pause, reset, and adjust the processing speed of the event feed

## Detection Logic

Each login event is scored against four rules. The scores add up, and the total determines the alert's severity.

| Condition | Points |
|---|---|
| Failed login | 30 |
| After-hours login (outside 7:00 AM – 7:00 PM) | 15 |
| Login from a suspicious country | 40 |
| Unrecognized device | 50 |

| Severity | Score |
|---|---|
| 🟢 Low | < 30 |
| 🟡 Medium | 30 – 69 |
| 🔴 High | ≥ 70 |

## Getting Started

### Prerequisites

- Python 3.9+

### Installation

```bash
git clone <your-repo-url>
cd "User Login Security"
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Usage

Run the generator and the dashboard in two separate terminals:

**Terminal 1 — start the event generator:**
```bash
python login_generator.py
```

**Terminal 2 — start the dashboard:**
```bash
streamlit run login_check.py
```

Then open the dashboard in your browser (Streamlit defaults to `http://localhost:8501`) and click **Start** to begin processing the live feed.

## Tech Stack

- [Python](https://www.python.org/)
- [Streamlit](https://streamlit.io/) — dashboard UI
- [Pandas](https://pandas.pydata.org/) — data handling
- [SQLite](https://www.sqlite.org/) — shared event store between the generator and dashboard
- [Faker](https://faker.readthedocs.io/) — synthetic login data generation

## Motivation

This project started as a way to learn front-end/UI development in Python using Streamlit, after having mostly worked on back-end logic before. The goal was to build something that mirrors a real SOC dashboard closely enough that a security analyst could recognize the workflow — live data coming in, risk being scored automatically, and alerts surfaced by severity.

## Possible Future Enhancements

- Alert triage states (New / Acknowledged / Resolved)
- Geographic breakdown of login activity
- "Impossible travel" detection (same user, two distant countries, short time window)
- Persisted alert history across sessions

## Author

Kyle Hoot

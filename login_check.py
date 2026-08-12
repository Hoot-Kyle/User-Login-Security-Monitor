import sqlite3
import time as pytime
from datetime import datetime
from datetime import time as dt_time
from pathlib import Path

import pandas as pd
import streamlit as st

# CONSTANTS/INITIALIZATION:
DB_PATH = Path(__file__).parent / "logins.db"

start_time = dt_time(7, 0)
end_time = dt_time(19, 0)

suspicious_countries = ("Russia", "China", "Iran", "North Korea")


def get_connection():
    conn = sqlite3.connect(DB_PATH, timeout=5)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS logins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            upn TEXT NOT NULL,
            country TEXT NOT NULL,
            device TEXT NOT NULL,
            successful INTEGER NOT NULL,
            login_time TEXT NOT NULL
        )
        """
    )
    return conn


# DETECTION LOGIC:
def analyze_login(row):

    findings = []
    risk_score = 0

    if not row["Successful"]:
        risk_score += 30
        findings.append("Failed Login")

    if row["Time"] < start_time or row["Time"] > end_time:
        risk_score += 15
        findings.append("After Hours Login")

    if row["Country"] in suspicious_countries:
        risk_score += 40
        findings.append("Suspicious Country")

    if "UNKNOWN" in row["Device"]:
        risk_score += 50
        findings.append("Unknown Device")

    return findings, risk_score


def risk_tier(score):
    if score < 30:
        return "Low"
    elif score < 70:
        return "Medium"
    return "High"


def hourly_summary(df):
    hours = []
    is_alert = []

    for _, r in df.iterrows():
        row = {
            "Country": r["country"],
            "Device": r["device"],
            "Successful": bool(r["successful"]),
            "Time": datetime.strptime(r["login_time"], "%H:%M:%S").time(),
        }
        _, score = analyze_login(row)
        hours.append(row["Time"].hour)
        is_alert.append(score > 0)

    summary = pd.DataFrame({"hour": hours, "alert": is_alert})
    grouped = summary.groupby("hour").agg(**{"Total Logins": ("alert", "size"), "Alerts": ("alert", "sum")})
    grouped = grouped.reindex(range(24), fill_value=0)
    grouped.index.name = "Hour of Day"
    return grouped


# SESSION STATE INITIALIZATION:
if "current_login" not in st.session_state:
    st.session_state.current_login = None

if "last_id" not in st.session_state:
    st.session_state.last_id = 0

if "alerts" not in st.session_state:
    st.session_state.alerts = []

if "running" not in st.session_state:
    st.session_state.running = False

# USER INTERFACE:
conn = get_connection()
df = pd.read_sql_query("SELECT * FROM logins ORDER BY id DESC LIMIT 200", conn)

st.title("User Login Security Monitor")
st.markdown("Developed by Kyle Hoot")
st.caption("Live feed — run `login_generator.py` in a separate terminal to stream in new logins.")

total_count = conn.execute("SELECT COUNT(*) FROM logins").fetchone()[0]
high_risk_alerts = sum(1 for a in st.session_state.alerts if a["score"] >= 70)

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Total Logins", total_count)
kpi2.metric("Processed", st.session_state.last_id)
kpi3.metric("Active Alerts", len(st.session_state.alerts))
kpi4.metric("High-Risk Alerts", high_risk_alerts)

st.dataframe(df)

st.subheader("Login Volume by Hour")
if df.empty:
    st.caption("No logins yet.")
else:
    st.bar_chart(hourly_summary(df))

speed = st.slider("Processing Speed (rows/sec)", 1, 10, 5)

if st.button("Start"):
    st.session_state.running = True

if st.button("Pause"):
    st.session_state.running = False

if st.button("Reset"):
    st.session_state.last_id = 0
    st.session_state.alerts = []
    st.session_state.current_login = None

# PROCESSING ENGINE:
if st.session_state.running:

    next_row = conn.execute(
        "SELECT id, upn, country, device, successful, login_time FROM logins "
        "WHERE id > ? ORDER BY id ASC LIMIT 1",
        (st.session_state.last_id,),
    ).fetchone()

    if next_row is not None:
        row_id, upn, country, device, successful, login_time = next_row

        row = {
            "UPN": upn,
            "Country": country,
            "Device": device,
            "Successful": bool(successful),
            "Time": datetime.strptime(login_time, "%H:%M:%S").time(),
        }

        st.session_state.current_login = row

        findings, risk_score = analyze_login(row)

        if risk_score > 0:
            alert = {"user": row["UPN"], "score": risk_score, "findings": findings}
            st.session_state.alerts.append(alert)

        st.session_state.last_id = row_id
    else:
        st.info("Waiting for new logins...")

    conn.close()
    pytime.sleep(1 / speed)
    st.rerun()

conn.close()

# DISPLAY:
st.subheader("Current Login Being Processed")

row = st.session_state.current_login

if row is not None:
    st.metric("User", row["UPN"])
    st.metric("Country", row["Country"])
    st.metric("Device", row["Device"])
    st.metric("Time", row["Time"].strftime("%H:%M:%S"))

st.subheader("Alerts")

filter_col, search_col = st.columns([2, 1])

tier_filter = filter_col.multiselect(
    "Filter by severity",
    options=["Low", "Medium", "High"],
    default=["Low", "Medium", "High"],
)
user_search = search_col.text_input("Filter by user")

visible_alerts = [
    a
    for a in reversed(st.session_state.alerts)
    if risk_tier(a["score"]) in tier_filter
    and user_search.lower() in a["user"].lower()
]

if not visible_alerts:
    st.caption("No alerts match the current filters.")

for alert in visible_alerts:
  score = alert["score"]
  message = (f"{alert['user']} | " f"Risk Score: {score} | " f"{', '.join(alert['findings'])}")

  if score < 30:
    st.success(message)

  elif score < 70:
    st.warning(message)

  else:
    st.error(message)

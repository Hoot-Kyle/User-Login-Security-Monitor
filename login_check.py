import pandas as pd
import streamlit as st
import time as pytime
from datetime import time as dt_time

# CONSTANTS/INITIALIZATION:
start_time = dt_time(7, 0)
end_time = dt_time(19, 0)

suspicious_countries = ("Russia", "China", "Iran", "North Korea")

if "current_login" not in st.session_state:
    st.session_state.current_login = None
row = None

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

# SESSION STATE INITIALIZATION:
if "current_row" not in st.session_state:
    st.session_state.current_row = 0

if "alerts" not in st.session_state:
    st.session_state.alerts = []

if "running" not in st.session_state:
    st.session_state.running = False

# USER INTERFACE:
df = pd.read_excel("Login Log.xlsx")

st.title("User Login Security Monitor")
st.markdown("Developed by Kyle Hoot")
st.dataframe(df)

speed = st.slider("Processing Speed (rows/sec)", 1, 10, 5)

st.metric("Processed", st.session_state.current_row)

if st.button("Start"):
    st.session_state.running = True

if st.button("Pause"):
    st.session_state.running = False

if st.button("Reset"):
    st.session_state.current_row = 0
    st.session_state.alerts = []

# PROCESSING ENGINE: 
if st.session_state.current_row >= len(df):
    st.session_state.running = False
    st.success("All login records have been processed.")
    st.stop()

if st.session_state.running:

    row = df.iloc[st.session_state.current_row]

    st.session_state.current_login = row 

    findings, risk_score = analyze_login(row)

    if risk_score > 0:
        alert = {"user": row["UPN"], "score": risk_score, "findings": findings}

        st.session_state.alerts.append(alert)

    st.session_state.current_row += 1
    pytime.sleep(1 / speed)
    st.rerun()

# DISPLAY:
st.subheader("Current Login Being Processed")

row = st.session_state.current_login

if row is not None:
    st.metric("User", row["UPN"])
    st.metric("Country", row["Country"])
    st.metric("Device", row["Device"])
    st.metric("Time", row["Time"].strftime("%H:%M:%S"))
 
st.subheader("Alerts")

for alert in st.session_state.alerts:
  score = alert["score"]
  message = (f"{alert['user']} | " f"Risk Score: {score} | " f"{', '.join(alert['findings'])}")

  if score < 30:
    st.success(message)

  elif score < 70:
    st.warning(message)

  else:
    st.error(message)

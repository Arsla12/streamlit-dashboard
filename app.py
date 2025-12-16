import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

st.set_page_config(
    page_title="Bridge Monitoring Dashboard",
    page_icon="🌉",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar
st.sidebar.header("Dashboard Controls")
selected_bridge = st.sidebar.selectbox("Select Bridge", ["Bridge A", "Bridge B", "Bridge C"])
time_range = st.sidebar.slider(
    "Select time range (minutes from start)",
    min_value=0,
    max_value=60,
    value=(0, 30),
    step=1
)
auto_refresh = st.sidebar.checkbox("Auto-refresh (5s)", value=False)

# Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Live Monitoring", 
    "🚨 Alerts", 
    "📈 Historical Analysis", 
    "🤖 ML Predictions"
])

# Hardcoded sensor data
timestamps = pd.date_range(datetime.now() - timedelta(minutes=60), periods=61, freq="1min")
sensor_ids = ["S1", "S2", "S3"]
data = pd.DataFrame({
    "timestamp": np.tile(timestamps, len(sensor_ids)),
    "sensor_id": np.repeat(sensor_ids, len(timestamps)),
    "value": np.random.rand(len(timestamps)*len(sensor_ids))*10 + 10,
    "rule_threshold": [15]*len(timestamps)*len(sensor_ids),
    "anomaly": [0]*len(timestamps)*len(sensor_ids),
    "traffic_load_proxy": np.random.randint(100, 200, len(timestamps)*len(sensor_ids))
})

# Display basic info in tab1
with tab1:
    st.header("Live Sensor Monitoring")
    filtered_data = data[(data['timestamp'] >= timestamps[time_range[0]]) & 
                         (data['timestamp'] <= timestamps[time_range[1]])]
    st.dataframe(filtered_data)

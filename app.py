import streamlit as st
import pandas as pd
import plotly.express as px

# ---------------- Page config ----------------
st.set_page_config(
    page_title="Bridge Monitoring Dashboard",
    page_icon="🌉",
    layout="wide"
)

# ---------------- Load data ----------------
@st.cache_data
def load_data():
    df = pd.read_csv(
        "data/ipmb_5sensors_30min_1_to_10hz.csv"
    )
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.dropna(subset=["timestamp"])
    return df

df = load_data()

# ---------------- Title ----------------
st.title("🌉 Bridge Monitoring Dashboard")

# ---------------- Sidebar filters ----------------
st.sidebar.header("Filters")

selected_bridge = st.sidebar.selectbox(
    "Select Bridge",
    sorted(df["bridge_id"].unique())
)

start_time_all = df["timestamp"].min()
end_time_all = df["timestamp"].max()
max_minutes = int((end_time_all - start_time_all).total_seconds() // 60)

time_range = st.sidebar.slider(
    "Time Range (minutes from start)",
    min_value=0,
    max_value=max_minutes,
    value=(0, min(30, max_minutes)),
    step=1
)

start_time = start_time_all + pd.Timedelta(minutes=time_range[0])
end_time = start_time_all + pd.Timedelta(minutes=time_range[1])

# ---------------- Filter data ----------------
filtered_df = df[
    (df["bridge_id"] == selected_bridge) &
    (df["timestamp"] >= start_time) &
    (df["timestamp"] <= end_time)
]
st.subheader("📊 Live Sensor Plots")

# Choose which sensors to show
sensor_list = sorted(filtered_df["sensor_id"].unique())
selected_sensors = st.multiselect(
    "Select sensors",
    options=sensor_list,
    default=sensor_list
)

plot_df = filtered_df[filtered_df["sensor_id"].isin(selected_sensors)].copy()

# Line chart (one line per sensor)
fig = px.line(
    plot_df,
    x="timestamp",
    y="value",
    color="sensor_id",
    title="Sensor Values Over Time"
)

# Add threshold lines per sensor (if rule_threshold exists and is not null)
if "rule_threshold" in plot_df.columns:
    thresholds = (
        plot_df.dropna(subset=["rule_threshold"])
        .groupby("sensor_id")["rule_threshold"]
        .first()
        .to_dict()
    )
    for sid, thr in thresholds.items():
        fig.add_hline(y=float(thr), line_dash="dash", annotation_text=f"{sid} threshold")

# Highlight anomalies (if anomaly column exists)
if "anomaly" in plot_df.columns:
    anomaly_points = plot_df[plot_df["anomaly"] == 1]
    if not anomaly_points.empty:
        fig.add_scatter(
            x=anomaly_points["timestamp"],
            y=anomaly_points["value"],
            mode="markers",
            name="Anomalies",
            marker_symbol="x",
            marker_size=10
        )

st.plotly_chart(fig, use_container_width=True)

# ---------------- Display ----------------
st.subheader(f"Sensor Data — {selected_bridge}")
st.dataframe(filtered_df, use_container_width=True)

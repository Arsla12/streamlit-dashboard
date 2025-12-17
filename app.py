import streamlit as st
import pandas as pd

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

# ---------------- Display ----------------
st.subheader(f"Sensor Data — {selected_bridge}")
st.dataframe(filtered_df, use_container_width=True)

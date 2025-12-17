import streamlit as st
import pandas as pd

st.set_page_config(page_title="Bridge Monitoring Dashboard", page_icon="🌉", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_csv(
        "data/ipmb_5sensors_30min_1_to_10hz.csv",
        parse_dates=["timestamp"]
    )
    return df

df = load_data()

st.title("🌉 Bridge Monitoring Dashboard")

st.sidebar.header("Filters")

selected_bridge = st.sidebar.selectbox(
    "Select Bridge",
    sorted(df["bridge_id"].unique())
)

min_time = df["timestamp"].min()
max_time = df["timestamp"].max()

time_range = st.sidebar.slider(
    "Time Range",
    min_value=min_time,
    max_value=max_time,
    value=(min_time, max_time)
)

filtered_df = df[
    (df["bridge_id"] == selected_bridge) &
    (df["timestamp"] >= time_range[0]) &
    (df["timestamp"] <= time_range[1])
]

st.subheader(f"Sensor Data — {selected_bridge}")
st.dataframe(filtered_df, use_container_width=True)

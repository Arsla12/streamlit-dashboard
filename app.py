import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

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
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Live Monitoring",
    "🚨 Alerts",
    "📈 Historical Analysis",
    "🤖 ML Predictions"
])
with tab1:
    st.subheader("Live Sensor Monitoring")
    st.subheader("📊 Live Sensor Plots (per sensor)")

    sensor_list = sorted(filtered_df["sensor_id"].unique())
    selected_sensors = st.multiselect(
        "Select sensors",
        options=sensor_list,
        default=sensor_list
    )

    plot_df = filtered_df[filtered_df["sensor_id"].isin(selected_sensors)].copy()

    # Create rows of 2 columns
    for i in range(0, len(selected_sensors), 2):
        cols = st.columns(2)

        for col_idx, sid in enumerate(selected_sensors[i:i+2]):
            with cols[col_idx]:
                s_df = plot_df[plot_df["sensor_id"] == sid].sort_values("timestamp")

                unit = ""
                if "unit" in s_df.columns and s_df["unit"].notna().any():
                    unit = str(s_df["unit"].dropna().iloc[0])

                fig = go.Figure()

                fig.add_trace(
                    go.Scatter(
                        x=s_df["timestamp"],
                        y=s_df["value"],
                        mode="lines",
                        name=sid
                    )
                )

                if "rule_threshold" in s_df.columns and s_df["rule_threshold"].notna().any():
                    thr = float(s_df["rule_threshold"].dropna().iloc[0])
                    fig.add_hline(y=thr, line_dash="dash", annotation_text="Threshold")

                if "anomaly" in s_df.columns:
                    a_df = s_df[s_df["anomaly"] == 1]
                    if not a_df.empty:
                        fig.add_trace(
                            go.Scatter(
                                x=a_df["timestamp"],
                                y=a_df["value"],
                                mode="markers",
                                name="Anomalies",
                                marker_symbol="x",
                                marker_size=10
                            )
                        )

                fig.update_layout(
                    title=f"Sensor {sid}",
                    xaxis_title="Time",
                    yaxis_title=f"Value ({unit})" if unit else "Value",
                    height=350,
                    showlegend=False
                )

                st.plotly_chart(fig, use_container_width=True)
# ---------------- Display ----------------
    st.subheader(f"Sensor Data — {selected_bridge}")
    st.dataframe(filtered_df, use_container_width=True)
with tab2:
    st.subheader("Alerts")
    st.info("Alerts logic will go here")

with tab3:
    st.subheader("Historical Analysis")
    st.info("Historical plots will go here")

with tab4:
    st.subheader("ML Predictions")
    st.info("ML predictions will go here")


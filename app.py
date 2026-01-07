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
max_minutes = int((end_time_all - start_time_all).total_seconds() // 60) + 1

time_range = st.sidebar.slider(
    "Time Range (minutes from start)",
    min_value=1,
    max_value=max_minutes,
    value=(1, min(30, max_minutes)),
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
    alerts_df = filtered_df.copy()
    total_points = len(alerts_df)

    if "anomaly" in alerts_df.columns and total_points > 0:
        anomaly_points = int((alerts_df["anomaly"] == 1).sum())
        normal_points = total_points - anomaly_points

        # ---------- TOP ROW: OVERVIEW ----------
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Data Points", total_points)
        col2.metric("Normal Points", normal_points)
        col3.metric("Anomaly Points", anomaly_points)

        st.markdown("---")

        # ---------- SEVERITY CALCULATION ----------
        critical_count = 0
        warning_count = 0

        if "rule_threshold" in alerts_df.columns and alerts_df["rule_threshold"].notna().any():
            valid_thr = alerts_df["rule_threshold"] > 0
            alerts_df = alerts_df[valid_thr].copy()

            alerts_df["exceed_ratio"] = (
                (alerts_df["value"] - alerts_df["rule_threshold"])
                / alerts_df["rule_threshold"]
            )

            critical_count = len(
                alerts_df[(alerts_df["value"] > alerts_df["rule_threshold"]) &
                          (alerts_df["exceed_ratio"] > 0.5)]
            )

            warning_count = len(
                alerts_df[(alerts_df["value"] > alerts_df["rule_threshold"]) &
                          (alerts_df["exceed_ratio"] <= 0.5)]
            )

        # ---------- SECOND ROW: SEVERITY ----------
        st.subheader("Alert Severity")

        col4, col5 = st.columns(2)
        col4.metric("🔴 Critical Alerts", critical_count)
        col5.metric("🟠 Warning Alerts", warning_count)

        st.markdown("---")

        # ---------- DETAILS TABLE ----------
        if anomaly_points > 0:
            st.subheader("Recent Anomalies")

            recent = (
                filtered_df[filtered_df["anomaly"] == 1]
                .sort_values("timestamp")
                .tail(50)
            )

            show_cols = [
                c for c in [
                    "timestamp", "sensor_id", "value", "unit",
                    "rule_threshold", "anomaly_type"
                ] if c in recent.columns
            ]

            st.dataframe(recent[show_cols], use_container_width=True)
        else:
            st.success("No anomalies detected in the selected time range.")

    else:
        st.warning("No anomaly information available in the dataset.")

with tab3:
    st.subheader("Historical Analysis")
    sensor_ids = sorted(filtered_df["sensor_id"].unique())
    selected_sensor = st.selectbox("Select sensor", sensor_ids)
    show_anomalies_only = st.checkbox("Show anomalies only", value=False)

    s_df = filtered_df[filtered_df["sensor_id"] == selected_sensor].sort_values("timestamp")

    if show_anomalies_only and "anomaly" in s_df.columns:
    s_df = s_df[s_df["anomaly"] == 1]

    unit = ""
    if "unit" in s_df.columns and s_df["unit"].notna().any():
        unit = str(s_df["unit"].dropna().iloc[0])

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=s_df["timestamp"], y=s_df["value"], mode="lines", name="Value"))

    # Threshold
    if "rule_threshold" in s_df.columns and s_df["rule_threshold"].notna().any():
        thr = float(s_df["rule_threshold"].dropna().iloc[0])
        fig.add_hline(y=thr, line_dash="dash", annotation_text="Threshold")

    # Anomalies
    if "anomaly" in s_df.columns:
        a_df = s_df[s_df["anomaly"] == 1]
        if s_df.empty:
    st.warning("No data available for this selection.")
    st.stop()
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
        title=f"Sensor {selected_sensor} — Historical Trend",
        xaxis_title="Time",
        yaxis_title=f"Value ({unit})" if unit else "Value",
        height=450,
        showlegend=False
    )

    st.plotly_chart(fig, use_container_width=True)
    st.subheader("Value Distribution")

hist = go.Figure()
hist.add_trace(
    go.Histogram(
        x=s_df["value"],
        nbinsx=30
    )
)

hist.update_layout(
    title="Histogram of Sensor Values",
    xaxis_title=f"Value ({unit})" if unit else "Value",
    yaxis_title="Count",
    height=350,
    showlegend=False
)

st.plotly_chart(hist, use_container_width=True)

    # Stats
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Mean", f"{s_df['value'].mean():.2f}")
    c2.metric("Std", f"{s_df['value'].std():.2f}")
    c3.metric("Min", f"{s_df['value'].min():.2f}")
    c4.metric("Max", f"{s_df['value'].max():.2f}")

with tab4:
    st.subheader("ML Predictions")
    st.info("ML predictions will go here")


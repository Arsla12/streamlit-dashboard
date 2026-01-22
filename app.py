import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

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

    s_df = (
        filtered_df[filtered_df["sensor_id"] == selected_sensor]
        .sort_values("timestamp")
    )

    if show_anomalies_only and "anomaly" in s_df.columns:
        s_df = s_df[s_df["anomaly"] == 1]

    if s_df.empty:
        st.warning("No data available for this selection.")
        st.stop()

    # ----- Unit detection -----
    unit = ""
    if "unit" in s_df.columns and s_df["unit"].notna().any():
        unit = str(s_df["unit"].dropna().iloc[0])

    # ----- Time series plot -----
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=s_df["timestamp"],
            y=s_df["value"],
            mode="lines",
            name="Value"
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
        title=f"Sensor {selected_sensor} — Historical Trend",
        xaxis_title="Time",
        yaxis_title=f"Value ({unit})" if unit else "Value",
        height=450,
        showlegend=False
    )

    st.plotly_chart(fig, use_container_width=True)

    # ----- Distribution (Histogram) -----
    st.subheader("Value Distribution")

    hist = go.Figure()
    hist.add_trace(go.Histogram(x=s_df["value"], nbinsx=30))

    hist.update_layout(
        xaxis_title=f"Value ({unit})" if unit else "Value",
        yaxis_title="Count",
        height=350,
        showlegend=False
    )

    st.plotly_chart(hist, use_container_width=True)

    # ----- Statistics -----
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Mean", f"{s_df['value'].mean():.2f}")
    c2.metric("Std", f"{s_df['value'].std():.2f}")
    c3.metric("Min", f"{s_df['value'].min():.2f}")
    c4.metric("Max", f"{s_df['value'].max():.2f}")

with tab4:
    st.subheader("ML Predictions")

    # ---------------- Imports (local) ----------------
    from ml.ml_scoring import MLScorer, get_risk_emoji

    # ---------------- Safety checks ----------------
    required_cols = {"sensor_id", "span_id", "sensor_type", "value", "timestamp"}
    missing = required_cols - set(filtered_df.columns)
    if missing:
        st.error(f"Missing required columns in dataset: {sorted(missing)}")
        st.stop()

    # ---------------- Controls ----------------
    cA, cB, cC, cD = st.columns([2, 2, 2, 2])
    with cA:
        selected_span = st.selectbox("Span", ["All"] + sorted(filtered_df["span_id"].unique()))
    with cB:
        window_size = st.slider("Window size (latest N points per sensor)", 20, 300, 50, 10)
    with cC:
        combine_rule = st.selectbox("Combine rule", ["Worst-case (max)", "Average (mean)"])
    with cD:
        show_only_flagged = st.checkbox("Show only flagged sensors", value=False)

    view_df = filtered_df.copy()
    if selected_span != "All":
        view_df = view_df[view_df["span_id"] == selected_span].copy()

    if view_df.empty:
        st.warning("No data for this selection.")
        st.stop()

    # ---------------- Helper functions ----------------
    def risk01_from_iforest(score: float, threshold: float | None) -> float:
        """
        IsolationForest decision_function: higher = more normal.
        Convert to risk [0,1] based on distance below threshold.
        """
        if threshold is None:
            return 0.0
        if score >= threshold:
            return 0.0
        dist = threshold - score
        return float(np.clip(dist / 0.2, 0.0, 1.0))  # 0.2 scaling is a practical default

    def risk_level_from_risk01(r: float) -> str:
        if r >= 0.85: return "critical"
        if r >= 0.65: return "high"
        if r >= 0.40: return "medium"
        return "low"

    def combine_risk(scores: pd.Series) -> float:
        scores = scores.dropna()
        if scores.empty:
            return float("nan")
        if combine_rule.startswith("Worst"):
            return float(scores.max())
        return float(scores.mean())

    # ---------------- Load scorers (cached) ----------------
    @st.cache_resource
    def get_if_scorer():
        return MLScorer(artifact_dir="ml_artifacts")

    if_scorer = get_if_scorer()

    # ---------------- Score per sensor (routes by sensor_type) ----------------
    per_sensor_rows = []

    grouped = view_df.sort_values("timestamp").groupby(["sensor_id", "span_id", "sensor_type"], as_index=False)

    for (sensor_id, span_id, sensor_type), g in grouped:
        if len(g) < window_size:
            continue
        recent = g.tail(window_size)

        # ---- 1) Strain gauge -> Isolation Forest (works now) ----
        if sensor_type == "strain_gauge":
            out = if_scorer.compute_risk_score(recent, span_id, sensor_type)
            raw = float(out.get("risk_score", np.nan))
            thr = out.get("threshold", None)
            has_model = bool(out.get("has_model", False))
            anomaly = bool(out.get("anomaly_detected", False))

            risk01 = risk01_from_iforest(raw, thr) if has_model else np.nan
            level = risk_level_from_risk01(risk01) if has_model else "unknown"

            per_sensor_rows.append({
                "sensor_id": sensor_id,
                "span_id": span_id,
                "sensor_type": sensor_type,
                "model_used": "Isolation Forest",
                "raw_score": raw,
                "threshold": thr,
                "risk_0_1": risk01,
                "risk_level": level,
                "flag": anomaly,
                "has_model": has_model
            })

        # ---- 2) Accelerometer -> CNN Autoencoder (placeholder until you wire cnn_scoring.py) ----
        elif sensor_type == "accelerometer_rms":
            # Professional: show it's part of your pipeline even if not wired yet
            per_sensor_rows.append({
                "sensor_id": sensor_id,
                "span_id": span_id,
                "sensor_type": sensor_type,
                "model_used": "1D CNN Autoencoder",
                "raw_score": np.nan,
                "threshold": np.nan,
                "risk_0_1": np.nan,
                "risk_level": "unwired",
                "flag": False,
                "has_model": False
            })

        else:
            per_sensor_rows.append({
                "sensor_id": sensor_id,
                "span_id": span_id,
                "sensor_type": sensor_type,
                "model_used": "Unknown",
                "raw_score": np.nan,
                "threshold": np.nan,
                "risk_0_1": np.nan,
                "risk_level": "unknown",
                "flag": False,
                "has_model": False
            })

    scores_df = pd.DataFrame(per_sensor_rows)

    if scores_df.empty:
        st.warning("No sensors scored. Expand the time range or reduce the window size.")
        st.stop()

    # Optional filter
    if show_only_flagged:
        scores_df = scores_df[scores_df["flag"] == True].copy()

    # ---------------- Combined view (span + bridge) ----------------
    span_combined = (
        scores_df.groupby("span_id", as_index=False)["risk_0_1"]
        .apply(lambda s: combine_risk(s))
        .rename(columns={"risk_0_1": "combined_risk_0_1"})
    )

    bridge_combined = combine_risk(scores_df["risk_0_1"])

    # ---------------- TOP: Executive summary cards ----------------
    # Unified CNN + Predictive CNN placeholders (until you wire them)
    unified_prob = np.nan   # later: fill from your unified CNN output
    forecast_risk = np.nan  # later: fill from predictive CNN output

    left, mid, right, far = st.columns(4)
    left.metric("Bridge combined risk (0–1)", "N/A" if np.isnan(bridge_combined) else f"{bridge_combined:.2f}")
    mid.metric("Sensors scored", len(scores_df))
    right.metric("Sensors flagged", int(scores_df["flag"].sum()))
    far.metric("Unified CNN anomaly prob", "Not wired" if np.isnan(unified_prob) else f"{unified_prob:.2f}")

    st.markdown("---")

    # ---------------- MIDDLE: Timeline chart (clean + professional) ----------------
    st.markdown("### Timeline")
    col1, col2 = st.columns([2, 1])

    with col2:
        sensor_choices = sorted(view_df["sensor_id"].unique())
        chart_sensor = st.selectbox("Sensor to plot", sensor_choices)

        show_model_overlay = st.checkbox("Overlay normalized risk (if available)", value=True)

    plot_df = view_df[view_df["sensor_id"] == chart_sensor].sort_values("timestamp").copy()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=plot_df["timestamp"], y=plot_df["value"], mode="lines", name="Sensor value"
    ))

    # Overlay risk_0_1 as a second y-axis (if we have it for that sensor)
    if show_model_overlay:
        r = scores_df[scores_df["sensor_id"] == chart_sensor]
        if not r.empty and pd.notna(r["risk_0_1"].iloc[0]):
            # flat line over time window (because we score per window)
            risk_val = float(r["risk_0_1"].iloc[0])
            fig.add_trace(go.Scatter(
                x=plot_df["timestamp"],
                y=[risk_val] * len(plot_df),
                mode="lines",
                name="Risk (0–1)",
                yaxis="y2"
            ))
            fig.update_layout(
                yaxis2=dict(
                    title="Risk (0–1)",
                    overlaying="y",
                    side="right",
                    range=[0, 1]
                )
            )

    fig.update_layout(
        height=450,
        xaxis_title="Time",
        yaxis_title="Value",
        legend=dict(orientation="h")
    )
    with col1:
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # ---------------- BOTTOM: Model breakdown table ----------------
    st.markdown("### Model Breakdown (Per Sensor)")

    scores_df["status"] = scores_df["risk_level"].apply(get_risk_emoji) + " " + scores_df["risk_level"]

    st.dataframe(
        scores_df[
            ["span_id", "sensor_id", "sensor_type", "model_used", "raw_score", "threshold",
             "risk_0_1", "status", "flag", "has_model"]
        ].sort_values(["flag", "risk_0_1"], ascending=[False, False]),
        use_container_width=True
    )

    st.markdown("### Combined by Span")
    st.dataframe(
        span_combined.sort_values("combined_risk_0_1", ascending=False),
        use_container_width=True
    )

    # ---------------- Model details (professional, minimal) ----------------
    with st.expander("Model Details"):
        st.markdown(
            """
            **Models used**
            - **Isolation Forest (Unsupervised)** — Strain gauge sensors → anomaly score (lower = more anomalous)
            - **1D CNN Autoencoder (Unsupervised)** — Accelerometer sensors → reconstruction error (higher = anomaly)
            - **Unified 1D CNN (Supervised)** — all sensors → anomaly probability [0,1]
            - **Predictive 1D CNN (Supervised)** — all sensors → future anomaly risk (0–100%)
            """
        )



import streamlit as st

# Page config
st.set_page_config(
    page_title="Bridge Monitoring Dashboard",
    layout="wide"
)

# Title
st.title("🌉 Bridge Monitoring Dashboard")

# Sidebar
st.sidebar.header("Filters")

# Example: select a bridge
bridge_options = ["Bridge A", "Bridge B", "Bridge C"]
selected_bridge = st.sidebar.selectbox("Select a Bridge:", bridge_options)

# Display selection
st.write(f"You have selected: **{selected_bridge}**")

# Success message
st.success("Sidebar is working!")


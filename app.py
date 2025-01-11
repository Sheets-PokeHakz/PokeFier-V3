import streamlit as st
import asyncio
from main import main, stop_autocatcher, TOKENS

# Streamlit UI
st.title("Pokefier Bot")
log_area = st.empty()  # Placeholder for logs

# Status Flags
if "bot_running" not in st.session_state:
    st.session_state.bot_running = False


# Function to read logs
def read_logs(file_path="logs/pokefier.log"):
    try:
        with open(file_path, "r") as log_file:
            return log_file.read()
    except FileNotFoundError:
        return "Log file not found."


# Start Button
if st.button("Start Bot"):
    if not st.session_state.bot_running:
        st.session_state.bot_running = True
        st.info("Starting bots...")

        # Start the bots asynchronously
        asyncio.run(main(TOKENS))
        st.success("Bots started!")

        # Display logs dynamically
        while st.session_state.bot_running:
            logs = read_logs()  # Read log file
            log_area.code(logs, language="text")
            asyncio.sleep(1)  # Refresh every second
    else:
        st.warning("Bots are already running.")

# Stop Button
if st.button("Stop Bot"):
    if st.session_state.bot_running:
        asyncio.run(stop_autocatcher())  # Stop bots asynchronously
        st.session_state.bot_running = False
        st.success("Bots stopped!")
    else:
        st.warning("Bots are not running.")

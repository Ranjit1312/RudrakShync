import streamlit as st
from modules import auth, assessment, profile, journal, streak

st.set_page_config(page_title="RudrakshYnc", layout="wide")

tabs = {
    "About Me": auth.show_about,
    "Assessment": assessment.show_assessment,
    "Profile + Practice": profile.show_profile,
    "Practice Log + Journaling": journal.show_journal,
    "Streak Tracker + Reports": streak.show_streak
}

st.sidebar.title("Navigation")
selected_tab = st.sidebar.radio("Go to", list(tabs.keys()))

# Check login status for restricted tabs
if selected_tab in ["Practice Log + Journaling", "Streak Tracker + Reports"]:
    if not st.session_state.get("user"):
        st.warning("Please log in to access this feature.")
        auth.login_ui()
    else:
        tabs[selected_tab]()
else:
    tabs[selected_tab]()

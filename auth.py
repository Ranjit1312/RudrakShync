import streamlit as st
import uuid

def ensure_session_id():
    """
    Generates a UUID-based session ID for anonymous users.
    Called once per session.
    """
    if "session_id" not in st.session_state:
        st.session_state["session_id"] = str(uuid.uuid4())

def login_ui():
    st.subheader("Log In or Sign Up")
    st.text_input("Email")
    st.text_input("Password", type="password")
    st.button("Log In")
    st.markdown("_(Add Supabase auth here)_")

def show_about():
    st.title("About RudrakshYnc")
    st.write("This app helps you sync with your inner self and rise daily.")
    st.markdown("Visit [YouTube](https://youtube.com) | Read the books")
    st.markdown("**Privacy**: We only store essential data. Journaling is private.")

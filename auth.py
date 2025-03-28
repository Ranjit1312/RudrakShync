import streamlit as st

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

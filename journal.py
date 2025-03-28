import streamlit as st

def show_journal():
    st.title("Practice Log & Reflection")
    st.text_area("Before Practice (What are you feeling?)")
    st.slider("Before Practice Intensity", 0, 10, 5)
    st.text_area("After Practice (What shifted?)")
    st.slider("How helpful was this practice?", 0, 10, 5)
    if st.button("Save Log"):
        st.success("Log saved. (Connect to Supabase here)")

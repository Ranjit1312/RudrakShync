import streamlit as st
import matplotlib.pyplot as plt

def show_profile():
    st.title("Your Profile")
    scores = st.session_state.get("assessment_scores", {})
    if not scores:
        st.warning("Please take the assessment first.")
        return
    fig, ax = plt.subplots()
    ax.pie(scores.values(), labels=scores.keys(), autopct='%1.1f%%')
    st.pyplot(fig)
    st.markdown("_(Recommend practice based on dominant or low scores here)_")

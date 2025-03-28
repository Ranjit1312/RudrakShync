import streamlit as st

def show_assessment():
    st.title("Neuro-Factor Assessment")
    st.write("Rate yourself on the following factors:")
    factors = ["Stress", "Mood", "Focus", "Social", "GABA", "Anxiety", "Motivation"]
    scores = {}
    for factor in factors:
        scores[factor] = st.slider(factor, 0, 10, 5)
    if st.button("Submit"):
        st.session_state["assessment_scores"] = scores
        st.success("Assessment saved for session.")

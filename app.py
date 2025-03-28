import streamlit as st
#from modules import auth, assessment, profile, journal, streak
import auth, assessment, profile, journal, streak

st.set_page_config(page_title="RudrakshYnc", layout="wide")

tabs = {
    "About Me": auth.show_about,
    "Assessment": assessment.run_assessment_flow,
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


# # app.py

# import streamlit as st
# from assessment_core import (
#     DOMAINS, initialize_scores, apply_microtask_results, apply_question_answer,
#     clamp_scores, finalize_conflict_resolution, compute_domain_confidence_label
# )

# def main():
#     st.title("Adaptive 7-Domain Wellness Assessment")

#     if "phase" not in st.session_state:
#         st.session_state.phase = 0  # we can increment the phase as we go
#     if "domain_scores" not in st.session_state:
#         scores, conf = initialize_scores()
#         st.session_state.domain_scores = scores
#         st.session_state.domain_conf = conf

#     # We'll also store if user had "consistently low confidence" throughout
#     if "low_confidence_counter" not in st.session_state:
#         st.session_state.low_confidence_counter = 0

#     # We'll store a microtask for 2 steps: microtask A and possibly microtask B
#     if "microtask_A_done" not in st.session_state:
#         st.session_state.microtask_A_done = False
#     if "microtask_B_done" not in st.session_state:
#         st.session_state.microtask_B_done = False

#     # We'll store intermediate "conflict_suspects" if needed:
#     if "microtask_suspects" not in st.session_state:
#         st.session_state.microtask_suspects = {}
#     if "user_selfreport_suspects" not in st.session_state:
#         st.session_state.user_selfreport_suspects = {}

#     # Helper function to handle confidence slider
#     def get_confidence_slider(question_label):
#         return st.slider(f"Confidence in your {question_label} answer?", 0, 100, 80) / 100.0

#     # Phase-based approach
#     if st.session_state.phase == 0:
#         st.subheader("Micro-Task A: Simulated Reaction Test (Color Reaction)")
#         st.write("Pretend you did a 20s color reaction test. Enter approximate results below:")

#         avg_rt = st.number_input("Avg Reaction Time (ms) [lower=better]", value=500, step=10)
#         false_alarms = st.number_input("False Alarms Count", value=0, step=1)
#         misses = st.number_input("Misses Count", value=0, step=1)
#         # We'll let user specify how confident they are in these reported stats
#         task_conf = st.slider("How confident/trustworthy are these microtask stats?", 0, 100, 90) / 100.0

#         if st.button("Next ->"):
#             task_data = {
#                 "avg_reaction_time": avg_rt,
#                 "false_alarms": false_alarms,
#                 "misses": misses,
#                 "task_type": "color"
#             }
#             apply_microtask_results(
#                 task_data=task_data,
#                 user_confidence=task_conf,
#                 domain_scores=st.session_state.domain_scores,
#                 domain_conf=st.session_state.domain_conf
#             )
#             st.session_state.microtask_A_done = True
#             st.session_state.phase = 1
#             st.experimental_rerun()

#     elif st.session_state.phase == 1:
#         st.subheader("Context & Arousal Check")

#         # Q1: Compare day vs usual
#         day_compare = st.radio(
#             "How does today compare to your usual baseline?",
#             ["Pretty typical", "Better/calmer", "Worse/tense/lower"]
#         )
#         c_slider_1 = get_confidence_slider("Day comparison")
#         if c_slider_1 < 0.3:
#             st.session_state.low_confidence_counter += 1

#         # Apply a small domain shift
#         if day_compare == "Better/calmer":
#             # mild + for mood or stress
#             apply_question_answer("mood", +0.5, c_slider_1,
#                                   st.session_state.domain_scores,
#                                   st.session_state.domain_conf)
#         elif day_compare == "Worse/tense/lower":
#             # mild - to mood or + stress
#             apply_question_answer("mood", -0.5, c_slider_1,
#                                   st.session_state.domain_scores,
#                                   st.session_state.domain_conf)
#             apply_question_answer("stress", +0.5, c_slider_1,
#                                   st.session_state.domain_scores,
#                                   st.session_state.domain_conf)

#         # Q1a: Overall state
#         overall_state = st.selectbox(
#             "Current Overall State?",
#             ["Calm/relaxed", "Alert/energized", "Tense/jittery", "Tired/fatigued"]
#         )
#         c_slider_2 = get_confidence_slider("Arousal check")
#         if c_slider_2 < 0.3:
#             st.session_state.low_confidence_counter += 1

#         if overall_state == "Tense/jittery":
#             apply_question_answer("stress", +1.0, c_slider_2,
#                                   st.session_state.domain_scores,
#                                   st.session_state.domain_conf)
#             apply_question_answer("anxiety", +0.5, c_slider_2,
#                                   st.session_state.domain_scores,
#                                   st.session_state.domain_conf)
#         elif overall_state == "Tired/fatigued":
#             apply_question_answer("motivation", -1.0, c_slider_2,
#                                   st.session_state.domain_scores,
#                                   st.session_state.domain_conf)
#             apply_question_answer("focus", -0.5, c_slider_2,
#                                   st.session_state.domain_scores,
#                                   st.session_state.domain_conf)
#         elif overall_state == "Calm/relaxed":
#             apply_question_answer("gaba", +0.5, c_slider_2,
#                                   st.session_state.domain_scores,
#                                   st.session_state.domain_conf)
#         # alert => no big shift

#         if st.button("Next ->"):
#             st.session_state.phase = 2
#             st.experimental_rerun()

#     elif st.session_state.phase == 2:
#         st.subheader("Mood Check")

#         mood_scale = st.radio(
#             "Rate your emotional tone today",
#             ["Very positive", "Neutral/okay", "Mild negative/worried", "Strong negative/down"]
#         )
#         c_sl_mood = get_confidence_slider("mood rating")
#         if c_sl_mood < 0.3:
#             st.session_state.low_confidence_counter += 1

#         if mood_scale == "Very positive":
#             apply_question_answer("mood", +1.5, c_sl_mood,
#                                   st.session_state.domain_scores,
#                                   st.session_state.domain_conf)
#         elif mood_scale == "Neutral/okay":
#             apply_question_answer("mood", +0.0, c_sl_mood,
#                                   st.session_state.domain_scores,
#                                   st.session_state.domain_conf)
#         elif mood_scale == "Mild negative/worried":
#             apply_question_answer("mood", -0.5, c_sl_mood,
#                                   st.session_state.domain_scores,
#                                   st.session_state.domain_conf)
#         else: # strong negative
#             apply_question_answer("mood", -1.5, c_sl_mood,
#                                   st.session_state.domain_scores,
#                                   st.session_state.domain_conf)
#             apply_question_answer("anxiety", +0.5, c_sl_mood,
#                                   st.session_state.domain_scores,
#                                   st.session_state.domain_conf)

#         if st.button("Next ->"):
#             st.session_state.phase = 3
#             st.experimental_rerun()

#     elif st.session_state.phase == 3:
#         st.subheader("Social + Connection")
#         social_radio = st.radio(
#             "How connected did you feel recently?",
#             ["Very connected", "Somewhat", "Isolated/avoided contact"]
#         )
#         c_sl_social = get_confidence_slider("social rating")
#         if c_sl_social < 0.3:
#             st.session_state.low_confidence_counter += 1

#         if social_radio == "Very connected":
#             apply_question_answer("social", +1.5, c_sl_social,
#                                   st.session_state.domain_scores,
#                                   st.session_state.domain_conf)
#         elif social_radio == "Isolated/avoided contact":
#             apply_question_answer("social", -1.5, c_sl_social,
#                                   st.session_state.domain_scores,
#                                   st.session_state.domain_conf)

#         if st.button("Proceed ->"):
#             st.session_state.phase = 4
#             st.experimental_rerun()

#     elif st.session_state.phase == 4:
#         st.subheader("Adaptive Clarifier Logic")

#         # We'll do a simplistic approach: if stress domain_conf < 1.0 or domain is high, ask a clarifier:
#         clarifiers_needed = []
#         dscores = st.session_state.domain_scores
#         dconf = st.session_state.domain_conf

#         # Example logic:
#         if dscores["stress"] > 6 and dconf["stress"] < 2.0:
#             clarifiers_needed.append(("stress", "Do you experience racing thoughts or tension daily?"))
#         if dscores["focus"] < 4 and dconf["focus"] < 2.0:
#             clarifiers_needed.append(("focus", "Are you impulsively switching tasks or easily distracted?"))
#         if dscores["gaba"] < 4 and dconf["gaba"] < 2.0:
#             clarifiers_needed.append(("gaba", "Muscle tightness or insomnia from restless mind?"))
#         if dscores["anxiety"] > 6 and dconf["anxiety"] < 2.0:
#             clarifiers_needed.append(("anxiety", "Any panic or repeated worry loops?"))
#         if dscores["motivation"] < 4 and dconf["motivation"] < 2.0:
#             clarifiers_needed.append(("motivation", "Lack of drive, difficulty initiating tasks?"))

#         # We can show up to 2 clarifiers for simplicity:
#         max_clarifiers = 2
#         clarifier_responses = []
#         for i, (dom, question) in enumerate(clarifiers_needed[:max_clarifiers]):
#             st.write(f"**Clarifier for {dom.upper()}**")
#             answer = st.radio(question, ["No", "Yes", "Not sure"], key=f"clar_{dom}")
#             c_slider = get_confidence_slider(f"{dom} clarifier answer")
#             if c_slider < 0.3:
#                 st.session_state.low_confidence_counter += 1

#             if answer == "Yes":
#                 # e.g. +1 stress or -1 GABA etc.
#                 if dom == "stress":
#                     apply_question_answer("stress", +1.0, c_slider,
#                                           st.session_state.domain_scores,
#                                           st.session_state.domain_conf)
#                 elif dom == "focus":
#                     apply_question_answer("focus", -1.0, c_slider,
#                                           st.session_state.domain_scores,
#                                           st.session_state.domain_conf)
#                 elif dom == "gaba":
#                     apply_question_answer("gaba", -1.0, c_slider,
#                                           st.session_state.domain_scores,
#                                           st.session_state.domain_conf)
#                 elif dom == "anxiety":
#                     apply_question_answer("anxiety", +1.0, c_slider,
#                                           st.session_state.domain_scores,
#                                           st.session_state.domain_conf)
#                 elif dom == "motivation":
#                     apply_question_answer("motivation", -1.0, c_slider,
#                                           st.session_state.domain_scores,
#                                           st.session_state.domain_conf)
#             elif answer == "Not sure":
#                 # minimal shift, but add some partial effect
#                 if dom in ["stress", "anxiety"]:
#                     apply_question_answer(dom, +0.3, c_slider,
#                                           st.session_state.domain_scores,
#                                           st.session_state.domain_conf)
#                 elif dom in ["focus", "gaba", "motivation"]:
#                     apply_question_answer(dom, -0.3, c_slider,
#                                           st.session_state.domain_scores,
#                                           st.session_state.domain_conf)

#         # Potentially show micro-task B if user is uncertain in Focus or Anxiety
#         show_microtask_b = False
#         if st.session_state.low_confidence_counter >= 3:
#             # user is quite unconfident, let's rely more on micro-task B if focus is an issue
#             if dscores["focus"] < 5:
#                 show_microtask_b = True

#         # or if domain_conf["focus"] < 1.0 or domain_conf["anxiety"] < 1.0 => etc
#         # We'll just do a simple check:
#         if not st.session_state.microtask_B_done and show_microtask_b:
#             st.write("---")
#             st.subheader("Micro-Task B: 2-Back Simulation")
#             st.write("Enter approximate performance if you tried a 2-back test")

#             ms_2b = st.number_input("2-Back Misses Count", 0, 10, 2)
#             fa_2b = st.number_input("2-Back False Alarms", 0, 10, 1)
#             b_conf = st.slider("Confidence/trust in these 2-back stats?", 0, 100, 90) / 100.0

#             if st.button("Apply 2-Back Results"):
#                 task_data_b = {
#                     "avg_reaction_time": 500,  # ignoring for 2-back, or you can ask user
#                     "false_alarms": fa_2b,
#                     "misses": ms_2b,
#                     "task_type": "2back"
#                 }
#                 apply_microtask_results(task_data_b, b_conf,
#                                         st.session_state.domain_scores,
#                                         st.session_state.domain_conf)
#                 st.session_state.microtask_B_done = True
#                 st.experimental_rerun()

#         if st.button("Finalize Scores"):
#             st.session_state.phase = 5
#             st.experimental_rerun()

#     elif st.session_state.phase == 5:
#         st.subheader("Final Label & Summaries")
#         final_label = st.text_input("In one word, how would you label your mental state now?", "Okay")
#         st.write("Thank you. We'll finalize your domain scores now.")

#         # Optionally handle conflict resolution
#         # e.g. if domain_conf is low or microtask_suspects differ from user_suspects
#         # finalize_conflict_resolution(...) # If implementing a more advanced logic

#         # clamp scores
#         clamp_scores(st.session_state.domain_scores)

#         # Show results
#         st.write("## Final Domain Scores:")
#         domain_conf_labels = compute_domain_confidence_label(st.session_state.domain_conf)

#         for d in DOMAINS:
#             st.write(f"**{d.upper()}**: {st.session_state.domain_scores[d]:.1f} (Confidence: {domain_conf_labels[d]})")

#         if st.button("Reset Session"):
#             for key in list(st.session_state.keys()):
#                 del st.session_state[key]
#             st.experimental_rerun()


# if __name__ == "__main__":
#     main()

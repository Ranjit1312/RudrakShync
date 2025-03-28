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

# assessment_core.py

# import random

# # List of domain keys
# DOMAINS = ["stress", "mood", "focus", "social", "gaba", "anxiety", "motivation"]

# # Starting baseline for each domain
# BASELINE_SCORE = 5.0

# def initialize_scores():
#     """Initialize domain scores and domain confidence (0.0 to 1.0)."""
#     scores = {d: BASELINE_SCORE for d in DOMAINS}
#     confidences = {d: 0.0 for d in DOMAINS}  # We'll accumulate evidence
#     return scores, confidences

# def apply_microtask_results(task_data, user_confidence, domain_scores, domain_conf):
#     """
#     task_data: dict with fields like:
#       {
#         'avg_reaction_time': float,
#         'false_alarms': int,
#         'misses': int,
#         'task_type': 'color' or '2back'
#       }
#     user_confidence: 0 to 1 scale for the microtask result (though typically micro-task is objective,
#                      you can store a 'trust' factor or let user say how well they performed).
#     domain_scores: current domain scores
#     domain_conf: current domain confidence
#     """
#     # For demonstration, let's define some threshold-based logic:
#     avg_rt = task_data.get("avg_reaction_time", 500)
#     fa = task_data.get("false_alarms", 0)
#     ms = task_data.get("misses", 0)
#     ttype = task_data.get("task_type", "color")

#     # Example: color reaction or 2-back
#     if ttype == "color":
#         # if avg_rt < 400 => user is relatively quick => + to focus
#         if avg_rt < 400:
#             domain_scores["focus"] += 1.0 * user_confidence
#             domain_conf["focus"] += 0.3
#         elif avg_rt > 600:
#             # might be stressed or sluggish
#             domain_scores["focus"] -= 0.5 * user_confidence
#             domain_conf["focus"] += 0.3

#         # false alarms => might indicate impulsivity => low GABA
#         if fa > 2:
#             domain_scores["gaba"] -= 1.0 * user_confidence
#             domain_conf["gaba"] += 0.3

#         # misses => could be stress or focus problem
#         if ms > 2:
#             domain_scores["stress"] += 0.5 * user_confidence
#             domain_conf["stress"] += 0.3

#     elif ttype == "2back":
#         # e.g. if misses are high or user says they performed poorly => low focus
#         # or if they do well => high focus
#         if ms <= 1 and fa <= 1:
#             # good performance => + focus
#             domain_scores["focus"] += 1.5 * user_confidence
#             domain_conf["focus"] += 0.4
#         else:
#             domain_scores["focus"] -= 1.0 * user_confidence
#             domain_conf["focus"] += 0.4

#         # If false alarms > 2 => impulsivity => low GABA
#         if fa > 2:
#             domain_scores["gaba"] -= 1.0 * user_confidence
#             domain_conf["gaba"] += 0.4

# def apply_question_answer(domain, value_shift, q_confidence, domain_scores, domain_conf):
#     """
#     domain: domain key or list of domain keys
#     value_shift: how much we add or subtract from baseline
#     q_confidence: 0..1 slider indicating user confidence
#     domain_scores, domain_conf updated in place
#     """
#     if isinstance(domain, str):
#         domain = [domain]
#     for d in domain:
#         domain_scores[d] += value_shift * q_confidence
#         # Also boost confidence in that domain
#         domain_conf[d] += 0.2  # or some constant - each question can add some confidence

# def clamp_scores(domain_scores):
#     """Ensure final domain scores are in [0, 10]."""
#     for d in domain_scores:
#         if domain_scores[d] < 0:
#             domain_scores[d] = 0
#         elif domain_scores[d] > 10:
#             domain_scores[d] = 10

# def finalize_conflict_resolution(domain_scores, domain_conf, microtask_suspects, user_selfreport_suspects):
#     """
#     If there's a direct mismatch for a domain in microtask vs. self-report, 
#     favor whichever has higher confidence rating. Or if user had extremely low confidence 
#     overall, rely more on microtask data.
#     microtask_suspects = dict of domain -> microtask_value
#     user_selfreport_suspects = dict of domain -> selfreport_value
#     This is just an example approach, you can refine logic as needed.
#     """
#     for d in DOMAINS:
#         # If both microtask_suspects and user_selfreport_suspects contain domain
#         # and are contradictory, pick the one with higher domain_conf or specifically 
#         # a "microtask_conf" vs "self_conf" approach.
#         # We'll do a simple approach: if domain_conf[d] < 1.0 and we do have microtask_suspects,
#         # we might weigh the microtask_suspects more if it's strong.
#         pass
#     # For demonstration, not fully implemented.

# def compute_domain_confidence_label(domain_conf):
#     """
#     Return a label for each domain based on domain_conf value (0..some upper).
#     We'll treat > 1.5 as "High", between 0.5..1.5 as "Medium", <0.5 as "Low".
#     """
#     labels = {}
#     for d, c in domain_conf.items():
#         if c > 1.5:
#             labels[d] = "High"
#         elif c > 0.5:
#             labels[d] = "Medium"
#         else:
#             labels[d] = "Low"
#     return labels

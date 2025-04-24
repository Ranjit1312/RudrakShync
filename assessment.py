##########################
# assessment.py  •  24-Apr-2025
##########################
import json, time, statistics
from datetime import datetime
from typing import Dict, Any

import streamlit as st
import streamlit.components.v1 as components

from supabase_client import supabase      # ← make sure this helper exists
def _safe_rerun():
    """
    Call st.rerun() if available, fallback to st.experimental_rerun()
    for Streamlit < 1.10, or do nothing if neither exists.
    """
    if hasattr(st, "rerun"):
        st.rerun()
    elif hasattr(st, "experimental_rerun"):
        st.experimental_rerun()

# ------------------------------------------------------------------ #
#                       ──   CONST ANCHOR   ──                       #
# ------------------------------------------------------------------ #

DOMAINS = [
    "Stress", "Mood", "Focus", "Social", "GABA", "Anxiety", "Motivation",
]

# ── 1. Baseline & core question weights ──────────────────────────── #
BASE_WEIGHTS = {
    "Q2": {                       # “Right now, which word best describes…”
        "Calm":   {"Stress": -0.10, "GABA":  0.10},
        "Alert":  {},
        "Tense":  {"Stress":  0.10, "Anxiety": 0.10},
        "Tired":  {"Focus":  -0.10, "Motivation": -0.10},
    },

    "Mood":        {"Q3": 0.70, "Q4": 0.30},
    "Social":      {"Q5": 0.70, "Q6": 0.30},
    "Motivation":  {"Q7": 0.60, "Q8": 0.40},
    "Anxiety":     {"Q9": 0.70, "Q10": 0.30},
}

# ── 2. Go/No-Go weights (commission 70 %, omission 20 %, RT var 30 %) ─ #
GONOGO_WEIGHTS = {
    "commission": {"GABA":   -0.70},
    "omission":   {"Focus":  -0.20},
    "rt_var":     {"Stress":  0.30, "Anxiety": 0.30},
}

# ── 3. 2-Back weights (accuracy 60 %, RT var −20 % Stress / Anxiety) ── #
TWOBACK_WEIGHTS = {
    "accuracy": {"Focus":  0.60},
    "rt_var":   {"Stress": -0.20, "Anxiety": -0.20},
}

SUPABASE_TABLE = "assessments"

# ------------------------------------------------------------------ #
#                          ──   HELPERS   ──                         #
# ------------------------------------------------------------------ #
def init_session():
    """One-time Streamlit session initialisation."""
    if "scores" not in st.session_state:
        st.session_state.scores = {d: 5.0 for d in DOMAINS}
        st.session_state.conf   = {d: 0.0 for d in DOMAINS}
        st.session_state.started = False
        st.session_state.baseline_mod = 1.0
        st.session_state.user_data = {}

def update_scores(weight_map: Dict[str, float], multiplier: float = 1.0):
    """
    Apply deltas to the global score dict.
    `weight_map` already encodes direction (±) and proportion of influence.
    `multiplier` is a 0-1 normalised task metric (e.g. error-rate or accuracy).
    """
    for domain, weight in weight_map.items():
        delta = 10 * weight * multiplier   # 10-point scale
        st.session_state.scores[domain] += delta

def bump_conf(domain: str, delta: float = 0.1):
    st.session_state.conf[domain] = min(1.0, st.session_state.conf[domain] + delta)

# ------------------------------------------------------------------ #
#                    ──   QUESTION COMPONENTS   ──                   #
# ------------------------------------------------------------------ #
def q_baseline():
    """Q1  – baseline comparison  (± 5 % global modifier)"""
    opts = ["Better than usual", "Same as usual", "Worse than usual"]
    choice = st.radio("How does your current state compare to your usual baseline?", opts)
    if choice == opts[0]:
        st.session_state.baseline_mod = 1.05
    elif choice == opts[2]:
        st.session_state.baseline_mod = 0.95
    st.session_state.user_data["Q1"] = choice

def q_state_word():
    """Q2  – single-word state  (10 % weights)"""
    opts = ["Calm", "Alert", "Tense", "Tired"]
    choice = st.radio("Right now, which word best describes your state?", opts, horizontal=True)
    st.session_state.user_data["Q2"] = choice
    update_scores(BASE_WEIGHTS["Q2"][choice], 1.0)

# ---- Core self-report questions ----------------------------------- #
def q_mood_block():
    moods = ["Very Positive (+1)", "Neutral (0)", "Mild Negative (-0.5)", "Very Negative (-1)"]
    mood = st.radio("Q3  •  Rate your overall emotional tone **today**", moods)
    st.session_state.user_data["Q3"] = mood
    if "Positive" in mood:
        update_scores({"Mood": +10 * BASE_WEIGHTS["Mood"]["Q3"] / 10})
    elif "Mild Negative" in mood:
        update_scores({"Mood": -5 * BASE_WEIGHTS["Mood"]["Q3"] / 10})
    elif "Very Negative" in mood:
        update_scores({"Mood": -10 * BASE_WEIGHTS["Mood"]["Q3"] / 10})

    enjoy = st.radio(
        "Q4  •  Have you found **meaning or joy** in tasks recently?",
        ["Very often", "Occasionally", "Rarely", "Not at all"]
    )
    st.session_state.user_data["Q4"] = enjoy
    if enjoy in ("Rarely", "Not at all"):
        update_scores({"Mood": -10 * BASE_WEIGHTS["Mood"]["Q4"] / 10})
    elif enjoy == "Very often":
        update_scores({"Mood": +10 * BASE_WEIGHTS["Mood"]["Q4"] / 10})

def q_social_block():
    conn = st.radio("Q5  •  How **connected** do you feel to others lately?",
                    ["Very connected", "Somewhat connected", "Disconnected", "Isolated"])
    st.session_state.user_data["Q5"] = conn
    if conn == "Very connected":
        update_scores({"Social": +10 * BASE_WEIGHTS["Social"]["Q5"] / 10})
    elif conn in ("Disconnected", "Isolated"):
        update_scores({"Social": -10 * BASE_WEIGHTS["Social"]["Q5"] / 10})

    interact = st.radio("Q6  •  Have you had any **emotionally meaningful interaction** in the last 48 h?",
                        ["Yes", "No"], horizontal=True)
    st.session_state.user_data["Q6"] = interact
    if interact == "Yes":
        update_scores({"Social": +10 * BASE_WEIGHTS["Social"]["Q6"] / 10})

def q_motivation_block():
    mot = st.slider("Q7  •  How **energised / driven** do you feel to take action on your goals?",
                    -1.0, 1.0, 0.0, 0.05)
    st.session_state.user_data["Q7"] = mot
    update_scores({"Motivation": mot * BASE_WEIGHTS["Motivation"]["Q7"]})

    self_start = st.radio(
        "Q8  •  Do you often **initiate and complete tasks** without external pressure?",
        ["Yes, consistently", "Sometimes", "Rarely", "Not at all"]
    )
    st.session_state.user_data["Q8"] = self_start
    if self_start == "Yes, consistently":
        update_scores({"Motivation": +10 * BASE_WEIGHTS["Motivation"]["Q8"] / 10})
    elif self_start in ("Rarely", "Not at all"):
        update_scores({"Motivation": -10 * BASE_WEIGHTS["Motivation"]["Q8"] / 10})

def q_anxiety_block():
    anx = st.radio("Q9  •  How much **worry or internal restlessness** have you felt in the last 24 h?",
                   ["None", "Mild", "Moderate", "Severe"])
    st.session_state.user_data["Q9"] = anx
    if anx == "None":
        pass
    elif anx == "Mild":
        update_scores({"Anxiety": +3 * BASE_WEIGHTS["Anxiety"]["Q9"]})
    elif anx == "Moderate":
        update_scores({"Anxiety": +7 * BASE_WEIGHTS["Anxiety"]["Q9"]})
    else:
        update_scores({"Anxiety": +10 * BASE_WEIGHTS["Anxiety"]["Q9"]})

    avoid = st.radio("Q10 •  Have you **avoided** anything due to fear or worry recently?",
                     ["No", "Minor avoidance", "Moderate avoidance", "Yes, avoided important things"])
    st.session_state.user_data["Q10"] = avoid
    if avoid != "No":
        level = ["Minor avoidance", "Moderate avoidance", "Yes, avoided important things"].index(avoid) + 1
        update_scores({"Anxiety": level * 3 * BASE_WEIGHTS["Anxiety"]["Q10"]})

# ------------------------------------------------------------------ #
#                      ──   TASK A  (Go/No-Go)   ──                   #
# ------------------------------------------------------------------ #
def embed_gonogo():
    """Launch the Go/No-Go HTML/JS and wait for postMessage payload."""
    st.subheader("Micro-task A • Go / No-Go")
    st.caption("Tap/Press **SPACE** for GREEN disks, ignore RED disks (30 s).")

    with open("script/microtask_go_nogo.html") as f:
        html_code = f.read()

    result = components.html(f"""
        <script>
        window.addEventListener("message", (event) => {{
            if (event.data?.type === "gonogo_results") {{
                const payload = JSON.stringify(event.data.data);
                window.parent.postMessage({{ type: "streamlit:setComponentValue", value: payload }}, "*");
            }}
        }});
        </script>
        {html_code}
    """, height=600)

    data = st.experimental_get_query_params().get("gonogo_results", [None])[0]
    return json.loads(data) if data else None

def score_gonogo(results: dict):
    """
    Score Go/No-Go using 70/20/30 % domain split.
    results expected keys:
       correctHits, misses, falseAlarms, reactionTimes (list)
    """
    hits  = results.get("correctHits", 0)
    miss  = results.get("misses", 0)
    fa    = results.get("falseAlarms", 0)
    rts   = results.get("reactionTimes", [])
    total = hits + miss + fa if (hits + miss + fa) else 1

    commission_rate = fa   / total       # 0-1
    omission_rate   = miss / total       # 0-1
    rt_var          = (statistics.stdev(rts) / statistics.mean(rts)) if len(rts) > 1 else 0.0
    rt_norm         = min(rt_var / 0.4, 1.0)   # clamp at ≈400 % CV

    update_scores(GONOGO_WEIGHTS["commission"], commission_rate)
    update_scores(GONOGO_WEIGHTS["omission"],   omission_rate)
    update_scores(GONOGO_WEIGHTS["rt_var"],     rt_norm)

    if commission_rate > 0.2: bump_conf("GABA", 0.2)
    if omission_rate   > 0.2: bump_conf("Focus", 0.2)
    bump_conf("Stress", 0.2); bump_conf("Anxiety", 0.2)

# ------------------------------------------------------------------ #
#                      ──   TASK B  (2-Back)   ──                    #
# ------------------------------------------------------------------ #
def embed_twoback():
    st.subheader("Micro-task B • 2-Back Memory")
    st.caption("Press **SPACE** whenever the letter matches the one from 2 steps earlier.")

    with open("script/microtask_2back.html") as f:
        html_code = f.read()

    components.html(f"""
        <script>
        window.addEventListener("message", (event) => {{
            if (event.data?.type === "twoback_results") {{
                const payload = JSON.stringify(event.data.data);
                window.parent.postMessage({{ type: "streamlit:setComponentValue", value: payload }}, "*");
            }}
        }});
        </script>
        {html_code}
    """, height=600)

    data = st.experimental_get_query_params().get("twoback_results", [None])[0]
    return json.loads(data) if data else None

def score_twoback(results: dict):
    hits   = results.get("hits", 0)
    fa     = results.get("falseAlarms", 0)
    miss   = results.get("misses", 0)
    rts    = results.get("reactionTimes", [])
    total  = hits + fa + miss if (hits + fa + miss) else 1

    accuracy = hits / total
    rt_var   = (statistics.stdev(rts) / statistics.mean(rts)) if len(rts) > 1 else 0.0
    rt_norm  = min(rt_var / 0.4, 1.0)

    update_scores(TWOBACK_WEIGHTS["accuracy"], accuracy)
    update_scores(TWOBACK_WEIGHTS["rt_var"],    rt_norm)

    bump_conf("Focus",    0.3)
    bump_conf("Stress",   0.2)
    bump_conf("Anxiety",  0.2)

# ------------------------------------------------------------------ #
#                     ──   CLARIFIER QUESTIONS   ──                  #
# ------------------------------------------------------------------ #
def clarifiers():
    sus = [d for d in DOMAINS
           if st.session_state.conf[d] < 0.3
           or st.session_state.scores[d] > 7
           or st.session_state.scores[d] < 3][:2]

    for d in sus:
        st.subheader(f"Clarifier • {d}")
        if d in ("Stress", "Anxiety"):
            ans = st.radio(
                "Do you experience **racing thoughts, panic episodes or heart-pounding** related to stress / anxiety?",
                ["Never", "Sometimes", "Frequently"]
            )
            if ans == "Frequently":
                update_scores({ "Stress": 1.0, "Anxiety": 1.0 })
        elif d == "Motivation":
            ans = st.radio(
                "Do you lack drive to start tasks **or** feel no reward after finishing them?",
                ["No", "Yes"]
            )
            if ans == "Yes":
                update_scores({"Motivation": -1.0})
        elif d == "Focus":
            ans = st.radio(
                "Do you often switch tasks impulsively rather than staying consistent?",
                ["Consistent / focused", "Often switch impulsively"]
            )
            if ans == "Often switch impulsively":
                update_scores({"Focus": -1.0, "GABA": -0.5})
        elif d == "GABA":
            ans = st.radio(
                "Do you experience **muscle tightness** or difficulty relaxing daily?",
                ["No", "Occasionally", "Yes, frequently"]
            )
            if ans == "Yes, frequently":
                update_scores({"GABA": -1.0})
        st.markdown("---")
        bump_conf(d, 0.4)

# ------------------------------------------------------------------ #
#                        ──   FINAL PAGE   ──                        #
# ------------------------------------------------------------------ #
def final_page():
    st.header("All done – thank you!")
    st.text_input("Q11  •  In a single word or phrase, how would you describe your current mental state?",
                  key="Q11")

    conf_slider = st.slider("Q12 •  How **confident** are you in your responses today?",
                            0.0, 1.0, 0.7, 0.05, key="Q12")
    st.session_state.user_data["Q12"] = conf_slider

    # Apply ±5 % baseline global modifier
    for d in DOMAINS:
        st.session_state.scores[d] *= st.session_state.baseline_mod
        st.session_state.scores[d] = max(0.0, min(10.0, st.session_state.scores[d]))

    st.markdown("### Your Domain Scores")
    for d in DOMAINS:
        conf_label = ("Low" if st.session_state.conf[d] < 0.3
                      else "High" if st.session_state.conf[d] > 0.8 else "Medium")
        st.write(f"**{d}**: {st.session_state.scores[d]:.2f}   (Confidence: {conf_label})")

    if st.button("Show my results »"):
        persist_to_supabase()
        time.sleep(0.3)
        st.switch_page("practice.py")

# ------------------------------------------------------------------ #
#                 ──   SUPABASE  PERSISTENCE   ──                    #
# ------------------------------------------------------------------ #
def persist_to_supabase():
    session_id = st.session_state.get("session_id")
    user_email = st.session_state.get("user_email",None)

    payload = {
        "user_email": user_email,
        "session_id": session_id,
        "timestamp": datetime.utcnow().isoformat(),
        "scores": st.session_state.scores,
        "confidence": st.session_state.conf,
        "source": "assessment",
        "raw": st.session_state.user_data,
    }
    try:
        supabase.table(SUPABASE_TABLE).insert(payload).execute()
        st.success("Assessment saved to Supabase.")
    except Exception as e:
        st.error(f"Supabase error: {e}")

# ------------------------------------------------------------------ #
#                  ──   MAIN  FLOW  CONTROLLER   ──                  #
# ------------------------------------------------------------------ #
def run_assessment_flow():
    init_session()
    st.title("Neuro-Factor Assessment")

    if not st.session_state.started:
        st.markdown("""
        ##### 7 Neurobiological Factors we’ll profile
        • Stress / Arousal  
        • Mood  
        • Focus / Executive Function  
        • Social Bonding  
        • Inhibitory Tone (GABA)  
        • Anxiety / Fear Reactivity  
        • Motivation / Drive  
        """)
        if st.button("Start Assessment", use_container_width=True):
            st.session_state.started = True
            _safe_rerun()
        st.stop()

    # ----------------------  Flow begins  ----------------------- #
    q_baseline(); st.markdown("---")
    q_state_word(); st.markdown("---")

    # ---- Micro-task A ---- #
    gonogo = embed_gonogo()
    if gonogo:
        score_gonogo(gonogo)
        st.success("Go/No-Go processed."); st.markdown("---")

    # ---- Core questions ---- #
    q_mood_block();        st.markdown("---")
    q_social_block();      st.markdown("---")
    q_motivation_block();  st.markdown("---")
    q_anxiety_block();     st.markdown("---")

    # ---- Clarifiers ---- #
    clarifiers(); st.markdown("---")

    # ---- Optional 2-Back ---- #
    if st.session_state.conf["Focus"] < 0.5 or st.session_state.conf["Anxiety"] < 0.5:
        twoback = embed_twoback()
        if twoback:
            score_twoback(twoback)
            st.success("2-Back processed."); st.markdown("---")

    # ---- Final reflection / save ---- #
    final_page()

# ------------------------------------------------------------------ #
#  If this file is run directly:  streamlit run assessment.py         #
# ------------------------------------------------------------------ #
if __name__ == "__main__":
    run_assessment_flow()

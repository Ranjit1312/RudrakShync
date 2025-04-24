##########################
# assessment.py  •  24-Apr-2025
##########################
import json, time, statistics
from datetime import datetime
from typing import Dict, Any, List

import streamlit as st
import streamlit.components.v1 as components
from streamlit_javascript import st_javascript
from supabase_client import supabase   # ← provides a ready supabase instance

# ------------------------------------------------------------------ #
#   Streamlit re-run shim (keeps code compatible with old versions)  #
# ------------------------------------------------------------------ #
def _safe_rerun():
    if hasattr(st, "rerun"):
        st.rerun()
    elif hasattr(st, "experimental_rerun"):
        st.experimental_rerun()

# ------------------------------------------------------------------ #
#                       ──   CONST ANCHOR   ──                       #
# ------------------------------------------------------------------ #
DOMAINS = [
    "Stress", "Mood", "Focus", "Social", "GABA", "Anxiety", "Motivation"
]

BASE_WEIGHTS = {
    "Q2": {
        "Calm":   {"Stress": -0.10, "GABA":  0.10},
        "Alert":  {},
        "Tense":  {"Stress":  0.10, "Anxiety": 0.10},
        "Tired":  {"Focus":  -0.10, "Motivation": -0.10},
    },
    "Mood":       {"Q3": 0.70, "Q4": 0.30},
    "Social":     {"Q5": 0.70, "Q6": 0.30},
    "Motivation": {"Q7": 0.60, "Q8": 0.40},
    "Anxiety":    {"Q9": 0.70, "Q10": 0.30},
}

GONOGO_WEIGHTS = {
    "commission": {"GABA":   -0.70},
    "omission":   {"Focus":  -0.20},
    "rt_var":     {"Stress":  0.30, "Anxiety": 0.30},
}

TWOBACK_WEIGHTS = {
    "accuracy": {"Focus":  0.60},
    "rt_var":   {"Stress": -0.20, "Anxiety": -0.20},
}

SUPABASE_TABLE = "assessments"

# ------------------------------------------------------------------ #
#                        ──   STATE HELPERS   ──                     #
# ------------------------------------------------------------------ #
def init_session():
    if "step" not in st.session_state:
        st.session_state.step = -1                      # start-screen
        st.session_state.scores = {d: 5.0 for d in DOMAINS}
        st.session_state.conf   = {d: 0.0 for d in DOMAINS}
        st.session_state.baseline_mod = 1.0
        st.session_state.user_data: Dict[str, Any] = {}
        st.session_state.clarifiers: List[str] = []
        st.session_state.need_twoback = False

def update_scores(weight_map: Dict[str, float], multiplier: float = 1.0):
    for d, w in weight_map.items():
        st.session_state.scores[d] += 10 * w * multiplier  # 10-point scale

def bump_conf(domain: str, delta: float = 0.2):
    st.session_state.conf[domain] = min(1.0, st.session_state.conf[domain] + delta)

# ------------------------------------------------------------------ #
#                     ──   INDIVIDUAL PAGES   ──                     #
# ------------------------------------------------------------------ #
def page_start():
    st.title("Neuro-Factor Assessment")
    st.markdown("""
    ##### 7 factors we’ll profile
    • Stress / Arousal  
    • Mood  
    • Focus / Executive Function  
    • Social Bonding  
    • Inhibitory Tone (GABA)  
    • Anxiety / Fear Reactivity  
    • Motivation / Drive  
    """)
    if st.button("Start Assessment", use_container_width=True):
        st.session_state.step = 0
        _safe_rerun()

# ------------------------------------------------------------------ #
# 0 • Baseline (Q1) ------------------------------------------------- #
def page_baseline():
    opt = ["Better than usual", "Same as usual", "Worse than usual"]
    choice = st.radio("How does your current state compare to your usual baseline?", opt)
    st.session_state.user_data["Q1"] = choice
    st.session_state.baseline_mod = 1.05 if choice == opt[0] else 0.95 if choice == opt[2] else 1.0
    if st.button("Next »"):
        st.session_state.step += 1; _safe_rerun()

# 1 • State word (Q2) ---------------------------------------------- #
def page_state_word():
    opt = ["Calm", "Alert", "Tense", "Tired"]
    choice = st.radio("Right now, which word best describes your state?", opt, horizontal=True)
    st.session_state.user_data["Q2"] = choice
    update_scores(BASE_WEIGHTS["Q2"][choice])
    if st.button("Next »"):
        st.session_state.step += 1; _safe_rerun()

# 2 • Go / No-Go  --------------------------------------------------- #
# ------------------------------------------------------------------ #
# 2 • Go / No-Go  --------------------------------------------------- #
def page_gonogo():
    st.subheader("Micro-task A • Go / No-Go")
    st.caption("Press **SPACE** for GREEN discs, ignore RED discs (30 s).")

    # load and display HTML game
    with open("script/microtask_go_nogo.html", "r") as f:
        html_code = f.read()
    components.html(html_code, height=650, scrolling=True)
    # Poll the global variable that the task sets on Submit
    result_json = st_javascript("window.goNoGoPayload || null")

    if result_json and result_json != "null":
        results = json.loads(result_json)       # always a JSON string
        score_gonogo(results)
        st.success("Go/No-Go task recorded!")

        if st.button("Continue »"):
            st.session_state.step += 1
            _safe_rerun()
    else:
        st.info("Finish the task, hit **Submit**, then wait a second…")


def score_gonogo(r: dict):
    hits, miss, fa = r.get("correctHits",0), r.get("misses",0), r.get("falseAlarms",0)
    rts = r.get("reactionTimes",[])
    total = max(1, hits+miss+fa)

    com_rate = fa/total
    omi_rate = miss/total
    rt_var   = statistics.stdev(rts)/statistics.mean(rts) if len(rts)>1 else 0.0
    rt_norm  = min(rt_var/0.4,1.0)

    update_scores(GONOGO_WEIGHTS["commission"], com_rate)
    update_scores(GONOGO_WEIGHTS["omission"], omi_rate)
    update_scores(GONOGO_WEIGHTS["rt_var"], rt_norm)
    bump_conf("GABA"); bump_conf("Focus"); bump_conf("Stress"); bump_conf("Anxiety")

# 3 • Mood block ----------------------------------------------------- #
def page_mood():
    moods = ["Very Positive", "Neutral", "Mild Negative", "Very Negative"]
    mood = st.radio("Q3 • Rate your overall emotional tone today", moods)
    st.session_state.user_data["Q3"] = mood
    if mood == moods[0]:
        update_scores({"Mood": +10*BASE_WEIGHTS["Mood"]["Q3"]/10})
    elif mood == moods[2]:
        update_scores({"Mood": -5 *BASE_WEIGHTS["Mood"]["Q3"]})
    elif mood == moods[3]:
        update_scores({"Mood": -10*BASE_WEIGHTS["Mood"]["Q3"]/10})

    enjoy = st.radio("Q4 • Have you found meaning or joy in tasks recently?",
                     ["Very often","Occasionally","Rarely","Not at all"])
    st.session_state.user_data["Q4"] = enjoy
    if enjoy in ("Rarely","Not at all"):
        update_scores({"Mood": -10*BASE_WEIGHTS["Mood"]["Q4"]/10})
    elif enjoy == "Very often":
        update_scores({"Mood": +10*BASE_WEIGHTS["Mood"]["Q4"]/10})

    if st.button("Next »"):
        st.session_state.step += 1; _safe_rerun()

# 4 • Social block --------------------------------------------------- #
def page_social():
    conn = st.radio("Q5 • How connected do you feel to others lately?",
                    ["Very connected","Somewhat connected","Disconnected","Isolated"])
    st.session_state.user_data["Q5"] = conn
    if conn == "Very connected":
        update_scores({"Social": +10*BASE_WEIGHTS["Social"]["Q5"]/10})
    elif conn in ("Disconnected","Isolated"):
        update_scores({"Social": -10*BASE_WEIGHTS["Social"]["Q5"]/10})

    interact = st.radio("Q6 • Any emotionally meaningful interaction in last 48 h?",
                        ["Yes","No"], horizontal=True)
    st.session_state.user_data["Q6"] = interact
    if interact=="Yes":
        update_scores({"Social": +10*BASE_WEIGHTS["Social"]["Q6"]/10})

    if st.button("Next »"):
        st.session_state.step += 1; _safe_rerun()

# 5 • Motivation block ---------------------------------------------- #
def page_motivation():
    mot = st.slider("Q7 • How energised / driven do you feel to act on goals?",
                    -1.0, 1.0, 0.0, 0.05)
    st.session_state.user_data["Q7"] = mot
    update_scores({"Motivation": mot*BASE_WEIGHTS["Motivation"]["Q7"]})

    self_start = st.radio("Q8 • Do you initiate & complete tasks without pressure?",
                          ["Yes, consistently","Sometimes","Rarely","Not at all"])
    st.session_state.user_data["Q8"] = self_start
    if self_start=="Yes, consistently":
        update_scores({"Motivation": +10*BASE_WEIGHTS["Motivation"]["Q8"]/10})
    elif self_start in("Rarely","Not at all"):
        update_scores({"Motivation": -10*BASE_WEIGHTS["Motivation"]["Q8"]/10})

    if st.button("Next »"):
        st.session_state.step += 1; _safe_rerun()

# 6 • Anxiety block -------------------------------------------------- #
def page_anxiety():
    anx = st.radio("Q9 • Worry / internal restlessness in last 24 h",
                   ["None","Mild","Moderate","Severe"])
    st.session_state.user_data["Q9"] = anx
    if anx=="Mild":
        update_scores({"Anxiety": +3*BASE_WEIGHTS["Anxiety"]["Q9"]})
    elif anx=="Moderate":
        update_scores({"Anxiety": +7*BASE_WEIGHTS["Anxiety"]["Q9"]})
    elif anx=="Severe":
        update_scores({"Anxiety": +10*BASE_WEIGHTS["Anxiety"]["Q9"]/10})

    avoid = st.radio("Q10 • Have you avoided anything due to fear or worry?",
                     ["No","Minor avoidance","Moderate avoidance","Yes, important things"])
    st.session_state.user_data["Q10"] = avoid
    if avoid!="No":
        level = ["Minor avoidance","Moderate avoidance","Yes, important things"].index(avoid)+1
        update_scores({"Anxiety": level*3*BASE_WEIGHTS["Anxiety"]["Q10"]})

    if st.button("Next »"):
        # decide clarifiers/2-Back
        build_followup_plan()
        st.session_state.step += 1; _safe_rerun()

# ------------------------------------------------------------------ #
#               Clarifier plan & optional 2-Back                     #
# ------------------------------------------------------------------ #
def build_followup_plan():
    sus = [d for d in DOMAINS if st.session_state.conf[d]<0.3
           or st.session_state.scores[d]>7 or st.session_state.scores[d]<3]
    st.session_state.clarifiers = sus[:2]
    st.session_state.need_twoback = (
        st.session_state.conf["Focus"]<0.5 or st.session_state.conf["Anxiety"]<0.5
    )

def page_clarifier(domain: str):
    st.subheader(f"Clarifier • {domain}")
    if domain in ("Stress","Anxiety"):
        ans = st.radio("Racing thoughts, panic, heart-pounding episodes?",
                       ["Never","Sometimes","Frequently"])
        if ans=="Frequently":
            update_scores({"Stress":1.0,"Anxiety":1.0})
    elif domain=="Motivation":
        ans = st.radio("Lack drive or feel no reward after tasks?",["No","Yes"])
        if ans=="Yes":
            update_scores({"Motivation":-1.0})
    elif domain=="Focus":
        ans = st.radio("Often switch tasks impulsively?",["No","Yes"])
        if ans=="Yes":
            update_scores({"Focus":-1.0,"GABA":-0.5})
    elif domain=="GABA":
        ans = st.radio("Daily muscle tightness / difficulty relaxing?",
                       ["No","Occasionally","Yes, frequently"])
        if ans=="Yes, frequently":
            update_scores({"GABA":-1.0})
    bump_conf(domain)

    if st.button("Next »"):
        st.session_state.step += 1; _safe_rerun()

# ------------------------------------------------------------------ #
#  Optional 2-Back -------------------------------------------------- #
def page_twoback():
    st.subheader("Micro-task B • 2-Back Memory")
    st.caption("Press **SPACE** when the current letter matches the one 2 steps earlier.")

    with open("script/microtask_2back.html") as f:
        html_code = f.read()

    components.html(f"""
        <script>
        window.addEventListener("message",(e)=>{{
          if(e.data?.type==="twoback_results"){{
            const p=JSON.stringify(e.data.data);
            window.parent.postMessage({{type:"streamlit:setComponentValue",value:p}},"*");
          }}
        }});
        </script>{html_code}""", height=600)

    data = st.query_params.get("twoback_results", [None])[0]
    if data:
        score_twoback(json.loads(data))
        st.success("Task recorded!")
        if st.button("Continue »"):
            st.session_state.step += 1; _safe_rerun()
    else:
        st.info("The task is active below …")

def score_twoback(r: dict):
    hits, fa, miss = r.get("hits",0), r.get("falseAlarms",0), r.get("misses",0)
    rts=r.get("reactionTimes",[])
    total=max(1,hits+fa+miss)
    acc  = hits/total
    rtv  = statistics.stdev(rts)/statistics.mean(rts) if len(rts)>1 else 0.0
    rt_n = min(rtv/0.4,1.0)

    update_scores(TWOBACK_WEIGHTS["accuracy"], acc)
    update_scores(TWOBACK_WEIGHTS["rt_var"],    rt_n)
    bump_conf("Focus"); bump_conf("Stress"); bump_conf("Anxiety")

# ------------------------------------------------------------------ #
#  Final page ------------------------------------------------------- #
def page_final():
    st.header("All done – thank you!")
    st.text_input("In a single word or phrase, how would you describe your overall mental state?",
                  key="Q11")
    conf = st.slider("How confident are you in your responses today?",0.0,1.0,0.7,0.05)
    st.session_state.user_data["Q12"]=conf

    for d in DOMAINS:
        st.session_state.scores[d] = max(0.0,min(
            10.0, st.session_state.scores[d]*st.session_state.baseline_mod))

    st.markdown("### Your Domain Scores")
    for d in DOMAINS:
        label=("Low" if st.session_state.conf[d]<0.3 else
               "High" if st.session_state.conf[d]>0.8 else "Medium")
        st.write(f"**{d}** : {st.session_state.scores[d]:.2f}  (Confidence {label})")

    if st.button("Show my results »", use_container_width=True):
        save_to_supabase()
        time.sleep(0.3)
        st.switch_page("practice.py")

def save_to_supabase():
    payload = {
      "user_email": st.session_state.get("user_email"),
      "session_id": st.session_state.get("session_id"),
      "timestamp": datetime.utcnow().isoformat(),
      "scores": st.session_state.scores,
      "confidence": st.session_state.conf,
      "raw": st.session_state.user_data,
      "source": "assessment"
    }
    try:
        supabase.table(SUPABASE_TABLE).insert(payload).execute()
        st.success("Assessment saved.")
    except Exception as e:
        st.error(f"Supabase error: {e}")

# ------------------------------------------------------------------ #
#                       ──   PAGE DISPATCH   ──                      #
# ------------------------------------------------------------------ #
def run_assessment_flow():
    init_session()
    step = st.session_state.step

    # map step index → rendering function
    if step == -1:  page_start()
    elif step == 0: page_baseline()
    elif step == 1: page_state_word()
    elif step == 2: page_gonogo()
    elif step == 3: page_mood()
    elif step == 4: page_social()
    elif step == 5: page_motivation()
    elif step == 6: page_anxiety()
    # dynamic clarifier pages
    elif 7 <= step < 7 + len(st.session_state.clarifiers):
        idx = step - 7
        page_clarifier(st.session_state.clarifiers[idx])
    # possible 2-Back
    elif step == 7 + len(st.session_state.clarifiers) and st.session_state.need_twoback:
        page_twoback()
    # final summary
    else:
        page_final()

# ------------------------------------------------------------------ #
if __name__ == "__main__":
    run_assessment_flow()

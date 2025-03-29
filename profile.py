import streamlit as st
import matplotlib.pyplot as plt
import math
from supabase_client import supabase

############################
# Domain -> whether higher raw means negative
############################
DOMAIN_IS_INVERSE = {
    "Stress": True,
    "Anxiety": True,
    "Focus": False,
    "Motivation": False,
    "Mood": False,
    "Social": False,
    "GABA": False
}

def normalize_score(domain: str, raw_score: float) -> float:
    """
    Convert raw score [0..10] -> normalized [-1..+1], 
    factoring whether a higher raw score is good or bad.
    """
    if domain in DOMAIN_IS_INVERSE and DOMAIN_IS_INVERSE[domain]:
        # Higher raw => more negative
        # raw=0 => +1, raw=10 => -1
        return 1 - (raw_score / 5.0)
    else:
        # Higher raw => more positive
        # raw=0 => -1, raw=10 => +1
        return (raw_score / 5.0) - 1

def steps_for_abs_score(abs_s: float) -> int:
    """Decide how many steps to prescribe from 1..4 based on abs(normalized_score)."""
    if abs_s >= 0.75:
        return 4
    elif abs_s >= 0.50:
        return 3
    elif abs_s >= 0.25:
        return 2
    else:
        return 1

############################
# PSEUDO Supabase queries
############################
def fetch_practice(domain: str, polarity: str):
    """
    Return a single practice row for the domain & polarity.
    polarity is 'positive' or 'negative'.
    """
    # PSEUDO:
    practice = supabase.table("practices").select("*")\
        .eq("factor", domain)\
        .eq("polarity", polarity)\
        .single().execute()
    return practice.data
    # return {
    #     "id": 123,
    #     "factor": domain,
    #     "polarity": polarity,
    #     "title": f"{domain} ({polarity}) Practice",
    #     "description": f"Practice for {domain} with polarity {polarity}."
    # }

def fetch_practice_steps(practice_id: int):
    """
    Return all steps (1..4) for a practice from the practice_steps table.
    """
    # PSEUDO:
    steps = supabase.table("practice_steps").select("*")\
         .eq("practice_id", practice_id)\
         .order("step_number", ascending=True).execute()
    return steps.data
    # return [
    #     {
    #         "id": 1001,
    #         "practice_id": practice_id,
    #         "step_number": 1,
    #         "instruction": "Breathe deeply for 30s",
    #         "before_prompt": "How stressed do you feel before Step 1?",
    #         "after_prompt": "Any change after Step 1?"
    #     },
    #     {
    #         "id": 1002,
    #         "practice_id": practice_id,
    #         "step_number": 2,
    #         "instruction": "Focus on relaxing your muscles",
    #         "before_prompt": "Rate tension before Step 2",
    #         "after_prompt": "Note any difference after Step 2"
    #     },
    #     {
    #         "id": 1003,
    #         "practice_id": practice_id,
    #         "step_number": 3,
    #         "instruction": "Visualize a calming scene for 1 min",
    #         "before_prompt": "Optional reflection before Step 3",
    #         "after_prompt": "Describe your experience after Step 3"
    #     },
    #     {
    #         "id": 1004,
    #         "practice_id": practice_id,
    #         "step_number": 4,
    #         "instruction": "Final mindful breathing for 1 min",
    #         "before_prompt": "Check your readiness for final step",
    #         "after_prompt": "Final reflection"
    #     }
    # ]

def save_user_sequence(user_id, step_ids):
    """
    Insert a new record into user_sequences with the given array of step_ids.
    """
    # PSEUDO:
    supabase.table("user_sequences").insert({
        "user_id": user_id,
        "step_ids": step_ids
    }).execute()
    # pass

############################
# MAIN: show_profile
############################
def show_profile():
    st.title("Your Profile & Customized Practice")

    # 1) Check user
    user_email = st.session_state.get("user_email")
    if not user_email:
        st.warning("Please log in first to see your personalized profile.")
        return

    # 2) Fetch latest scores from Supabase
    try:
        response = supabase.table("assessments") \
            .select("scores, timestamp") \
            .or_(
                f"user_email.eq.{user_email},session_id.eq.{st.session_state['session_id']}"
            ) \
            .order("timestamp", desc=True) \
            .limit(1) \
            .execute()

        if not response.data or not response.data[0].get("scores"):
            st.warning("No past assessment found. Please take the assessment first.")
            return

        raw_scores = response.data[0]["scores"]

    except Exception as e:
        st.error(f"Error fetching scores: {e}")
        return

    # 3) Normalize scores => [-1..+1]
    norm_scores = {}
    for factor, raw_val in raw_scores.items():
        norm_scores[factor] = normalize_score(factor, raw_val)

    # 4) Create a pie chart based on absolute values
    abs_vals = [abs(v) for v in norm_scores.values() if v != 0]
    sum_abs = sum(abs_vals) if abs_vals else 1e-9  # avoid divide-by-zero
    labels = []
    pie_values = []
    colors = []
    for factor, val in norm_scores.items():
        # skip factors with val=0? or show them as 0% slice
        value_abs = abs(val)
        if value_abs > 0:
            pct = 100.0 * (value_abs / sum_abs)
        else:
            pct = 0.0
        labels.append(f"{factor} {val:+.2f} ({pct:.1f}%)")
        pie_values.append(value_abs)

        # color logic
        if val < 0:
            # negative domain => darker shade
            colors.append("dimgray")  # or "darkred", "gray", etc.
        else:
            # positive domain => brighter shade
            colors.append("lightgreen")  # or "yellowgreen", etc.

    fig, ax = plt.subplots()
    ax.pie(pie_values, labels=labels, colors=colors, autopct="%1.1f%%")
    st.pyplot(fig)
    st.markdown(
        "_Note: The percentages reflect the **absolute** normalized scores relative to the total._"
    )

    # 5) Find the minimal set of factors that covers >=50% of sum_abs
    # Sort by descending abs value
    sorted_factors = sorted(norm_scores.items(), key=lambda x: abs(x[1]), reverse=True)
    chosen_factors = []
    coverage = 0.0

    for factor, val in sorted_factors:
        chosen_factors.append((factor, val))
        coverage += abs(val)
        if coverage >= 0.5 * sum_abs:
            break

    st.subheader("Key Factors to Address (≥50% coverage)")
    st.write([f"{f} ({v:+.2f})" for f,v in chosen_factors])

    # 6) Build the user sequence of steps
    # We'll gather a list of all step IDs, plus a structure for the combined practice.
    all_step_ids = []
    # We'll store the practice steps in a structure grouped by step_number:
    # combined_steps[ step_number ] = [ { factor, step_data }, ... ]
    from collections import defaultdict
    combined_steps = defaultdict(list)

    for factor, val in chosen_factors:
        polarity = "positive" if val >= 0 else "negative"
        abs_s = abs(val)
        n_steps = steps_for_abs_score(abs_s)

        # fetch practice
        practice = fetch_practice(factor, polarity)
        if not practice:
            st.warning(f"No practice found for {factor} / {polarity}")
            continue

        # fetch practice steps
        steps_data = fetch_practice_steps(practice["id"])
        # slice only the first n_steps
        selected_steps = steps_data[:n_steps]

        # collect
        for s in selected_steps:
            step_num = s["step_number"]  # 1..4
            combined_steps[step_num].append({
                "factor": factor,
                "polarity": polarity,
                "practice_id": practice["id"],
                "step_id": s["id"],
                "instruction": s["instruction"],
                "before_prompt": s["before_prompt"],
                "after_prompt": s["after_prompt"]
            })
            all_step_ids.append(s["id"])

    # store user sequence in DB
    if all_step_ids:
        save_user_sequence(user_id, all_step_ids)

    # 7) Present 3-part flow: Journaling Before, Practice Steps, Journaling After
    st.subheader("Practice Session")

    ### 7a) Journaling Before
    st.markdown("### 1. Journaling Before")
    all_before_prompts = []
    for step_num, items in combined_steps.items():
        # each item might have a before_prompt
        for it in items:
            if it["before_prompt"]:
                all_before_prompts.append(f"**({it['factor']} - Step {step_num})** {it['before_prompt']}")
    if all_before_prompts:
        st.text_area("Please reflect on these before prompts:",
                     "\n\n".join(all_before_prompts),
                     key="journaling_before")
    else:
        st.write("*No specific before prompts.*")

    ### 7b) Practice Steps (up to 4 total)
    st.markdown("### 2. Practice Steps")
    max_step_num = max(combined_steps.keys()) if combined_steps else 0
    for step_num in range(1, max_step_num+1):
        items = combined_steps[step_num]
        if not items:
            continue

        st.markdown(f"#### Step {step_num}")
        # Combine instructions for all factors in this step
        combined_instructions = []
        for it in items:
            combined_instructions.append(f"- **{it['factor']}**: {it['instruction']}")
        st.write("\n".join(combined_instructions))
        st.write("---")

    ### 7c) Journaling After
    st.markdown("### 3. Journaling After")
    all_after_prompts = []
    for step_num, items in combined_steps.items():
        for it in items:
            if it["after_prompt"]:
                all_after_prompts.append(f"**({it['factor']} - Step {step_num})** {it['after_prompt']}")
    if all_after_prompts:
        st.text_area("Reflect on these after prompts:",
                     "\n\n".join(all_after_prompts),
                     key="journaling_after")
    else:
        st.write("*No specific after prompts.*")

    ### 7d) Improvement Slider
    # We only show it if user has typed something in "journaling_after" (as an example).
    if st.session_state.get("journaling_after"):
        improvement = st.slider("How much do you feel you've improved (0=none, 100=complete)?", 0, 100, 50)
        st.write(f"Improvement reported: {improvement}%")
    else:
        st.info("Please fill in your 'Journaling After' reflections above to enable the Improvement slider.")

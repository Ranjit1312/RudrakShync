##########################
# assessment.py
##########################
import streamlit as st
import streamlit.components.v1 as components
import json
# If you need typed dictionaries:
from typing import Dict, Any, Optional

class NeuroAssessment:
    """
    Manages domain scoring for 7 neurobiological factors:
    - Stress
    - Mood
    - Focus
    - Social
    - GABA
    - Anxiety
    - Motivation

    Scores are kept in self.domain_scores (0-10).
    Confidence stored in self.domain_conf (0.0 to 1.0).
    """

    def __init__(self):
        # Initialize domain scores at a 'neutral' 5, domain confidence at 0.
        self.domains = ["Stress", "Mood", "Focus", "Social", "GABA", "Anxiety", "Motivation"]
        self.domain_scores: Dict[str, float] = {d: 5.0 for d in self.domains}
        self.domain_conf: Dict[str, float] = {d: 0.0 for d in self.domains}

        # Store relevant user inputs / micro-task results in a dictionary
        self.user_data: Dict[str, Any] = {}

    def _update_domain(
        self,
        domain: str,
        delta_score: float,
        delta_conf: float = 0.1,
        confidence_slider: float = 1.0
    ):
        """
        Update the domain score and confidence.

        :param domain: Domain name, e.g. "Stress"
        :param delta_score: How much to increment/decrement (can be negative).
        :param delta_conf: How much to increment the domain confidence from this item.
        :param confidence_slider: The user’s own self-rated confidence (0 to 1).
        """
        if domain not in self.domain_scores:
            return

        # Weighted by user’s confidence
        effective_delta = delta_score * confidence_slider
        self.domain_scores[domain] += effective_delta

        # Increase domain confidence (capped at 1.0)
        self.domain_conf[domain] = min(1.0, self.domain_conf[domain] + delta_conf * confidence_slider)

    def run_microtask_and_get_results():
        """
        Embeds Microtask A and waits for postMessage with results.
        Returns: parsed results dict or None
        """
        st.subheader("Microtask A – Go/No-Go Reaction Test")
        st.write("Complete the task below. Press SPACE on green, ignore red.")
    
        # Read HTML content
        with open("microtask_go_nogo.html") as f:
            html_code = f.read()
    
        # Embed HTML and JS listener
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
    
        # Input field to capture streamlit:setComponentValue result
        result_json = st.experimental_get_query_params().get("gonogo_results", [None])[0]
        if result_json:
            try:
                return json.loads(result_json)
            except:
                st.error("Failed to parse microtask result.")
        return None
    
    # def run_twoback_microtask():
    #     with open("microtask_2back.html") as f:
    #         html_code = f.read()
    
    #     # Display and setup listener
    #     components.html(f"""
    #         <script>
    #         window.addEventListener("message", (event) => {{
    #             if (event.data?.type === "twoback_results") {{
    #                 const payload = JSON.stringify(event.data.data);
    #                 window.parent.postMessage({{ type: "streamlit:setComponentValue", value: payload }}, "*");
    #             }}
    #         }});
    #         </script>
    #         {html_code}
    #     """, height=600)
    
    #     result_json = st.experimental_get_query_params().get("twoback_results", [None])[0]
    #     if result_json:
    #         try:
    #             return json.loads(result_json)
    #         except:
    #             st.error("Failed to parse 2-Back result.")
    #     return None
        
    def record_microtask_a_results(
        self,
        reaction_time: float,
        hits: int,
        misses: int,
        false_alarms: int
    ):
        """
        Update domain scores based on Micro-Task A (Color Reaction).
        Example logic:
         - Good reaction time => +Focus
         - Many misses => -Focus or +Stress
         - Many false alarms => -GABA or +Impulsivity
        """
        # Placeholder thresholds: tweak or calibrate them with real data
        if reaction_time < 300:  # e.g. "fast" reaction
            # Slightly boost Focus
            self._update_domain("Focus", +1.0, delta_conf=0.2)
        else:
            # Possibly drop Focus or raise Stress
            self._update_domain("Focus", -0.5, delta_conf=0.1)

        if misses > 3:
            # Lower Focus or raise Stress
            self._update_domain("Focus", -1.0, delta_conf=0.1)
            self._update_domain("Stress", +0.5, delta_conf=0.1)

        if false_alarms > 2:
            # Possibly GABA deficiency or impulsivity
            self._update_domain("GABA", -1.0, delta_conf=0.2)

    def record_microtask_b_results(self, results: dict):
        """
        Update domain scores based on actual 2-Back micro-task results.
        Inputs: hits, falseAlarms, misses
        Scoring logic:
         - High misses => low focus or memory
         - High false alarms => impulsivity or poor inhibitory control
         - Good hits with low errors => improved Focus
        """
        hits = results.get("hits", 0)
        false_alarms = results.get("falseAlarms", 0)
        misses = results.get("misses", 0)
        total = hits + false_alarms + misses
    
        # Compute accuracy
        accuracy = hits / total if total else 0.0
    
        if accuracy >= 0.7 and false_alarms < 3:
            self._update_domain("Focus", +1.5, delta_conf=0.3)
        elif accuracy >= 0.5:
            self._update_domain("Focus", +0.5, delta_conf=0.2)
        else:
            self._update_domain("Focus", -1.0, delta_conf=0.2)
    
        if false_alarms > 3:
            self._update_domain("GABA", -0.5, delta_conf=0.2)
    
        if misses > 4:
            self._update_domain("Motivation", -0.5, delta_conf=0.1)

    def ask_context_and_arousal(self):
        """
        Q1 + Q1a: "How does today compare to your usual baseline?"
                  "What is your overall state?"
        Returns user choices and updates domain scores.
        """
        st.subheader("Context & Arousal")

        # Q1: "How does today compare..."
        q1_options = [
            "Feels pretty typical",
            "Notably better / calmer / more positive",
            "Notably worse / more tense / lower than usual"
        ]
        q1_choice = st.radio("How does today compare to your usual mood/energy baseline?", q1_options)
        conf_q1 = st.slider("How sure are you about your self-assessment? (Q1)", 0, 100, 80) / 100.0

        # Basic domain logic for Q1
        if q1_choice == q1_options[1]:
            # "Better" => possibly better Mood, less Stress
            self._update_domain("Mood", +1.0, confidence_slider=conf_q1)
            self._update_domain("Stress", -0.5, confidence_slider=conf_q1)
        elif q1_choice == q1_options[2]:
            # "Worse" => possibly higher Stress, lower Mood
            self._update_domain("Stress", +1.0, confidence_slider=conf_q1)
            self._update_domain("Mood", -1.0, confidence_slider=conf_q1)

        # Q1a: "What’s your overall state right now?"
        q1a_options = ["Calm/relaxed", "Alert/energized", "Tense/jittery", "Tired/fatigued"]
        q1a_choice = st.radio("What’s your overall state right now?", q1a_options)
        conf_q1a = st.slider("How sure are you about this self-assessment? (Q1a)", 0, 100, 80) / 100.0

        if q1a_choice == "Tense/jittery":
            self._update_domain("Stress", +1.0, confidence_slider=conf_q1a)
            self._update_domain("Anxiety", +0.5, confidence_slider=conf_q1a)
        elif q1a_choice == "Tired/fatigued":
            self._update_domain("Motivation", -1.0, confidence_slider=conf_q1a)
            self._update_domain("Focus", -0.5, confidence_slider=conf_q1a)
        elif q1a_choice == "Calm/relaxed":
            # Slightly reduce stress if user is calm
            self._update_domain("Stress", -0.5, confidence_slider=conf_q1a)

        # Store user input
        self.user_data["q1_choice"] = q1_choice
        self.user_data["q1a_choice"] = q1a_choice

    def ask_mood_check(self):
        """
        Q2: Mood rating
        """
        st.subheader("Mood Check")

        q2_options = [
            "Very positive/upbeat",
            "Neutral/okay",
            "Mild negative/worried",
            "Strong negative/down/anxious"
        ]
        mood_choice = st.radio("Rate your emotional tone today:", q2_options)
        conf_q2 = st.slider("How certain are you about this mood rating?", 0, 100, 80) / 100.0

        # Example scoring:
        if mood_choice == "Very positive/upbeat":
            self._update_domain("Mood", +1.5, confidence_slider=conf_q2)
        elif mood_choice == "Neutral/okay":
            pass  # no major shift
        elif mood_choice == "Mild negative/worried":
            self._update_domain("Mood", -1.0, confidence_slider=conf_q2)
        elif mood_choice == "Strong negative/down/anxious":
            self._update_domain("Mood", -2.0, confidence_slider=conf_q2)

        # Optional sub-item
        enjoyment_options = ["Yes, strongly", "A little", "Not really"]
        enjoyment_choice = st.radio("Are you enjoying or finding meaning in daily tasks?", enjoyment_options)
        conf_enjoy = st.slider("Confidence in that statement?", 0, 100, 80) / 100.0

        if enjoyment_choice == "Not really":
            self._update_domain("Mood", -1.0, confidence_slider=conf_enjoy)
            # Possibly also indicate lower Motivation
            self._update_domain("Motivation", -0.5, confidence_slider=conf_enjoy)
        elif enjoyment_choice == "Yes, strongly":
            self._update_domain("Mood", +1.0, confidence_slider=conf_enjoy)
            self._update_domain("Motivation", +0.5, confidence_slider=conf_enjoy)

        # Store user input
        self.user_data["mood_choice"] = mood_choice
        self.user_data["enjoyment_choice"] = enjoyment_choice

    def ask_social_connection(self):
        """
        Q3: Social + Connection
        """
        st.subheader("Social & Connection")

        social_options = [
            "Very connected",
            "Somewhat connected",
            "Isolated or avoided contact"
        ]
        social_choice = st.radio("How connected did you feel to others recently?", social_options)
        conf_social = st.slider("Confidence in your self-assessment (social)?", 0, 100, 80) / 100.0

        if social_choice == "Very connected":
            self._update_domain("Social", +1.0, confidence_slider=conf_social)
        elif social_choice == "Isolated or avoided contact":
            self._update_domain("Social", -1.0, confidence_slider=conf_social)
            # Possibly suspect mood or anxiety
            self._update_domain("Mood", -0.5, confidence_slider=conf_social)

        # Follow-Up
        supportive_interaction = st.radio("Any meaningful interactions or support you found helpful?", ["Yes", "No"])
        if supportive_interaction == "Yes":
            self._update_domain("Social", +0.5, confidence_slider=conf_social)

        # Store user input
        self.user_data["social_choice"] = social_choice
        self.user_data["supportive_interaction"] = supportive_interaction

    def maybe_ask_clarifiers(self):
        """
        Adaptive clarifiers for domains with high suspicion or low confidence.
        E.g. Stress/Anxiety clarifier, Motivation clarifier, Focus clarifier, GABA clarifier.
        We only ask the top 1-2 clarifiers that are truly needed.
        """

        # Identify top domains that are either uncertain (low confidence) or strongly flagged.
        # For demonstration, let's say if domain_conf < 0.3 or domain_scores < 4 or > 6, we might clarify.
        suspicious_domains = []
        for d in self.domains:
            if self.domain_conf[d] < 0.3:
                suspicious_domains.append(d)
            # Or if the domain score is quite high or low, we might want more clarity
            if self.domain_scores[d] > 7 or self.domain_scores[d] < 3:
                suspicious_domains.append(d)

        # Deduplicate domain list
        suspicious_domains = list(set(suspicious_domains))

        # Just ask up to 2 clarifiers to avoid user fatigue
        suspicious_domains = suspicious_domains[:2]

        for domain in suspicious_domains:
            st.subheader(f"Clarifier for {domain}")
            if domain in ["Stress", "Anxiety"]:
                clarifier_q = st.radio(
                    "Have you had episodes of racing thoughts, panic, or physical signs (heart pounding)?",
                    ["No", "Maybe", "Yes"]
                )
                clar_conf = st.slider(f"Confidence in your answer about {domain}?", 0, 100, 80) / 100.0
                if clarifier_q == "Yes":
                    self._update_domain("Anxiety", +1.0, confidence_slider=clar_conf)
                    self._update_domain("Stress", +1.0, confidence_slider=clar_conf)

            if domain == "Motivation":
                clarifier_q = st.radio(
                    "Do you lack the drive to start tasks, or do you do them but feel no reward?",
                    ["No", "Yes"]
                )
                clar_conf = st.slider("Confidence about motivation clarifier?", 0, 100, 80) / 100.0
                if clarifier_q == "Yes":
                    self._update_domain("Motivation", -1.0, confidence_slider=clar_conf)

            if domain == "Focus":
                clarifier_q = st.radio(
                    "Do you find yourself impulsively switching tasks, or are you consistent?",
                    ["Consistent/focused", "Often switch impulsively"]
                )
                clar_conf = st.slider("Confidence about focus clarifier?", 0, 100, 80) / 100.0
                if clarifier_q == "Often switch impulsively":
                    self._update_domain("Focus", -1.0, confidence_slider=clar_conf)
                    # Possibly GABA link
                    self._update_domain("GABA", -0.5, confidence_slider=clar_conf)

            if domain == "GABA":
                clarifier_q = st.radio(
                    "Do you experience muscle tightness or difficulty relaxing daily?",
                    ["No", "Occasionally", "Yes, frequently"]
                )
                clar_conf = st.slider("Confidence about GABA clarifier?", 0, 100, 80) / 100.0
                if clarifier_q == "Yes, frequently":
                    self._update_domain("GABA", -1.0, confidence_slider=clar_conf)

            st.markdown("---")  # Just a separator

    def maybe_run_microtask_b(self):
        """
        If Focus or Anxiety still uncertain after clarifiers, we can run Micro-Task B.
        This is where you'd embed your 2-Back or Go/No-Go logic (task_2.html).
        """
       # Check if the user needs more clarity
        need_focus_test = (self.domain_conf["Focus"] < 0.5)
        need_anxiety_test = (self.domain_conf["Anxiety"] < 0.5)
    
        if need_focus_test or need_anxiety_test:
            st.subheader("Micro-Task B: 2-Back Memory Test")
            st.write("Press SPACE when a letter matches the one from 2 steps ago. Complete the task below:")
    
            with open("microtask_2back.html") as f:
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
    
            result_json = st.experimental_get_query_params().get("twoback_results", [None])[0]
            if result_json:
                try:
                    results = json.loads(result_json)
                    self.record_microtask_b_results(results)
                    st.success("Micro-task B results processed.")
                except Exception as e:
                    st.error(f"Error parsing results: {e}")

    def final_check_and_label(self):
        """
        Q8: Single-word label, final normalization of domain scores, plus summary.
        """
        st.subheader("Final Quick Reflection")
        single_word = st.text_input("In a single word, how do you label your overall mental state?")
        self.user_data["final_label"] = single_word

        # Normalize domain scores to 0–10
        for d in self.domains:
            if self.domain_scores[d] < 0:
                self.domain_scores[d] = 0.0
            elif self.domain_scores[d] > 10:
                self.domain_scores[d] = 10.0

        # Summarize
        st.markdown("### Your Domain Scores")
        for d in self.domains:
            # Confidence interpretation
            conf_label = "Low" if self.domain_conf[d] < 0.3 else \
                         "High" if self.domain_conf[d] > 0.8 else "Medium"
            st.write(f"**{d}**: {self.domain_scores[d]:.2f} (Confidence: {conf_label})")

        # Optional: you can store or return these for later usage
        st.success("Assessment complete! You can now move to recommended practices or login.")

    #######################
    # Public method that runs the entire flow
    #######################
    def run_full_assessment(self):
        """
        Runs a full assessment flow in a linear sequence.
        You can break this up across multiple tabs or pages in your main app if you prefer.
        """

        st.header("Neuro-Factor Assessment")

        # 1. Micro-Task A
        st.subheader("Micro-Task A: Color Reaction Test")
        st.write("""
        Below is a short color reaction test. 
        Press spacebar when you see **Green**. 
        Do **not** press when you see **Red**.
        """)
        # For demonstration, we just simulate user input of micro-task results.
        # In a real deployment, embed the HTML/JS and capture data.
        results = self.run_microtask_and_get_results()
        if results:
            avg_rt = sum(results["reactionTimes"]) / max(1, len(results["reactionTimes"]))
            hits = results["correctHits"]
            misses = results["misses"]
            false_alarms = results["falseAlarms"]
            self.record_microtask_a_results(avg_rt, hits, misses, false_alarms)

        st.markdown("---")

        # 2. Q1 + Q1a
        self.ask_context_and_arousal()
        st.markdown("---")

        # 3. Mood Check
        self.ask_mood_check()
        st.markdown("---")

        # 4. Social + Connection
        self.ask_social_connection()
        st.markdown("---")

        # 5. Adaptive clarifiers
        self.maybe_ask_clarifiers()
        st.markdown("---")

        # 6. (Potential) Micro-Task B
        self.maybe_run_microtask_b()
        st.markdown("---")

        # 7. Final Label & Summaries
        self.final_check_and_label()


##########################
# Streamlit Page or Utility Function
##########################
def run_assessment_flow():
    """
    Demonstration function to run the entire assessment from start to finish
    in a single Streamlit page.
    """
    st.title("Assessment")
    assessment = NeuroAssessment()
    assessment.run_full_assessment()

    # If you need the final results:
    final_scores = assessment.domain_scores
    final_conf = assessment.domain_conf
    st.write("**Final Scores**: ", final_scores)
    st.write("**Final Confidences**: ", final_conf)

    # Save to Supabase
    if st.button("Save Assessment"):
        session_id = st.session_state.get("session_id")
        user_email = st.session_state.get("user_email", None)
        
        entry = {
            "user_email": user_email,
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat(),
            "scores": final_scores,
            "confidence": final_conf,
            "source": "assessment"
        }
      
        try:
            supabase.table("assessments").insert(entry).execute()
            st.success("Assessment saved successfully.")
        except Exception as e:
            st.error(f"Error saving assessment: {e}")

    # You can return them for further usage:
    # return final_scores, final_conf


# If you want to test in isolation: 
# if __name__ == "__main__":
#     import streamlit as st
#     run_assessment_flow()

import streamlit as st
from openai import OpenAI
import json
import requests
import uuid

# --- CONFIG & RESET ---
def reset_app():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# --- COGNITIVE TASK HELPERS ---
def check_cognitive_answer():
    if st.session_state.cognitive_answer == "Option 4":
        st.session_state.cognitive_score = 100
        st.session_state.cognitive_feedback = "Korrekt! Logische Schlussfolgerung richtig."
    else:
        st.session_state.cognitive_score = 0
        st.session_state.cognitive_feedback = "Falsch. Logische Schlussfolgerung nicht korrekt."
    st.session_state.step = "abi_grade"
    st.rerun()

# --- MAIN APP ---
def main():
    st.set_page_config(page_title="SEK-Auswahl Diagnostik-Demo", page_icon="👮‍♂️", layout="centered")
    
    # Initialisierung der Zustände
    if "step" not in st.session_state:
        st.session_state.step = "cognitive_task" # Startet jetzt mit kognitiver Aufgabe
        st.session_state.messages = []
        st.session_state.abi_score = 2.0      # Standardwert für Abi-Note
        st.session_state.self_score = 3       # Standardwert für Fragebogen
        st.session_state.cognitive_score = None # Score für kognitive Aufgabe
        st.session_state.cognitive_feedback = ""

    # --- PHASE 1: KOGNITIVE AUFGABE ---
    if st.session_state.step == "cognitive_task":
        st.title("Schritt 1: Kognitive Leistungsfähigkeit 🧠")
        st.write("Bitte lösen Sie die folgende logische Aufgabe schnell und präzise:")
        st.markdown("""
        **Welches Symbol vervollständigt die Reihe logisch?**
        
        [□ | ○ | △]  →  [○ | △ | □]  →  [△ | □ | ? ]
        
        """)
        
        # Simulierte Antwortoptionen
        options = ["Option 1: □", "Option 2: △", "Option 3: ◊", "Option 4: ○"]
        st.radio("Ihre Antwort:", options, key="cognitive_answer")
        
        # Button ruft die Check-Funktion auf, die den Score setzt und zum nächsten Schritt springt
        st.button("Antwort abgeben & weiter 🚀", on_click=check_cognitive_answer, use_container_width=True)

    # --- PHASE 2: ABITURNOTE ---
    elif st.session_state.step == "abi_grade":
        st.title("Schritt 2: Schulische Leistung (Abiturnote) 🎓")
        st.write("Bitte geben Sie Ihre Abschlussnote des Abiturs an:")
        st.info("Hinweis: Eine gute Abiturnote korreliert oft mit kognitiver Grundfähigkeit, aber für SEK-Einsätze sind andere Faktoren oft wichtiger.")
        
        st.session_state.abi_score = st.number_input(
            "Abiturnote (z.B. 1.0 bis 4.0):",
            min_value=1.0,
            max_value=4.0,
            value=2.0,
            step=0.1,
            format="%.1f"
        )
        
        if st.button("Weiter zum Fragebogen 📝", use_container_width=True):
            st.session_state.step = "questionnaire"
            st.rerun()

    # --- PHASE 3: FRAGEBOGEN (1 ITEM) ---
    elif st.session_state.step == "questionnaire":
        st.title("Schritt 3: Persönlichkeits-Fragebogen 🛡️")
        st.write("Bitte geben Sie an, wie sehr Sie der folgenden Aussage zustimmen:")
        
        st.session_state.self_score = st.select_slider(
            "Ich behalte auch in extrem stressigen Situationen einen kühlen Kopf und handle besonnen.",
            options=[1, 2, 3, 4, 5],
            value=3,
            format_func=lambda x: {1: "1 - Gar nicht stressresistent", 2: "2", 3: "3", 4: "4", 5: "5 - Sehr stressresistent"}[x]
        )
        
        if st.button("Weiter zum Kurz-Interview 🎤", use_container_width=True):
            st.session_state.step = "chat"
            st.session_state.messages = [
                {
                    "role": "system", 
                    "content": "Du bist ein psychologischer Diagnostiker für eine Polizeispezialeinheit (SEK). Du interviewst einen Bewerber kurz zum Thema Stressresistenz und Teamfähigkeit unter Extrembedingungen. Stelle prägnante, direkte, bohrende Fragen. Halte dich kurz."
                },
                {
                    "role": "assistant", 
                    "content": "Willkommen zum Mini-Interview. Erzählen Sie mir von einer Situation, in der Sie physisch oder psychisch an Ihre absoluten Grenzen gestoßen sind. Wie haben Sie reagiert und was haben Sie daraus gelernt?"
                }
            ]
            st.rerun()

    # --- PHASE 4: SHORT CHAT (MAX 2 INTERAKTIONEN) ---
    elif st.session_state.step == "chat":
        st.title("Schritt 4: Interview 💬")
        
        user_msgs_count = len([m for m in st.session_state.messages if m["role"] == "user"])
        st.progress(user_msgs_count / 2, text=f"Fortschritt: Frage {user_msgs_count} von 2")
        
        for msg in st.session_state.messages:
            if msg["role"] != "system":
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

        if user_msgs_count >= 2:
            st.success("Das Interview ist beendet.")
            if st.button("Mechanische Urteilsbildung starten 📊", type="primary", use_container_width=True):
                st.session_state.step = "results"
                st.rerun()
        else:
            if prompt := st.chat_input("Ihre Antwort eingeben..."):
                st.session_state.messages.append({"role": "user", "content": prompt})
                
                if user_msgs_count == 0:
                    client = OpenAI(api_key=st.secrets["openai"]["api_key"])
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=st.session_state.messages
                    )
                    st.session_state.messages.append({"role": "assistant", "content": response.choices[0].message.content})
                
                st.rerun()

    # --- PHASE 5: AUSWERTUNG & INTEGRATION ---
    elif st.session_state.step == "results":
        st.title("Schritt 5: Diagnostisches Urteil 🧠📊")
        
        if "ai_verdict" not in st.session_state:
            with st.spinner("Der diagnostische Algorithmus verrechnet die Daten..."):
                try:
                    client = OpenAI(api_key=st.secrets["openai"]["api_key"])
                    chat_text = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages if m["role"] != "system"])
                    
                    # Neuer Prompt, der alle 4 Datenquellen verrechnet
                    prompt_integration = f"""
                    Du bist ein hochentwickelter diagnostischer Algorithmus zur Verrechnung multimethodaler Daten für das Auswahlverfahren einer Polizeispezialeinheit (SEK).
                    Dir liegen vier unterschiedliche Datenquellen vor:
                    1. Kognitive Basisleistung (Logik-Test, Score 0-100): {st.session_state.cognitive_score} ({st.session_state.cognitive_feedback})
                    2. Schulische Leistung (Abiturnote, wobei 1.0 am besten ist): {st.session_state.abi_score}
                    3. Selbstbericht Stressresistenz (Skala 1-5, wobei 5 extrem hoch ist): {st.session_state.self_score}
                    4. Transkribiertes Kurz-Interview (fokussiert auf Extrembelastung):
                    {chat_text}
                    
                    Deine Aufgabe ist die mechanische Urteilsbildung (Prognose). Schätze die Wahrscheinlichkeit (0-100%) ein, mit der diese Person die **physischen und psychischen Extrembelastungen der SEK-Basisausbildung erfolgreich bewältigt**.
                    Beachte die Gewichtung: Für den SEK-Dienst sind physische Robustheit, psychische Stabilität und Teamfähigkeit (aus Interview und Selbstbericht ableitbar) oft wichtiger als rein akademische Leistung (Abiturnote). Die kognitive Grundleistung ist ein notwendiges Fundament.
                    
                    Gib die Antwort AUSSCHLIESSLICH als valides JSON-Objekt mit exakt diesen fünf Keys aus:
                    "prognose_prozent": (Als Integer, z.B. 75),
                    "begruendung_kognition": (Ein kurzer Satz, wie das Logik-Testergebnis einfließt),
                    "begruendung_abinote": (Ein kurzer Satz, wie die Abiturnote einfließt, ggf. Relativierung),
                    "begruendung_selbstbericht": (Ein kurzer Satz, wie der Selbstbericht zur Stressresistenz einfließt),
                    "begruendung_interview": (Ein kurzer Satz, welches Sprachmuster/Erlebnis im Interview ausschlaggebend war)
                    """
                    
                    res = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": prompt_integration}],
                        response_format={"type": "json_object"}
                    )
                    st.session_state.ai_verdict = json.loads(res.choices[0].message.content)
                except Exception as e:
                    st.error(f"Fehler bei der Berechnung: {e}")
                    st.session_state.ai_verdict = {
                        "prognose_prozent": 50, 
                        "begruendung_kognition": "Fehler",
                        "begruendung_abinote": "Fehler bei der Berechnung",
                        "begruendung_selbstbericht": "Fehler", 
                        "begruendung_interview": "Fehler"
                    }

        # Visualisierung des Ergebnisses
        v = st.session_state.ai_verdict
        prob = v.get("prognose_prozent", 50)
        
        st.markdown(f"### Eignungsprognose:")
        st.markdown(f"#### Wahrscheinlichkeit, die SEK-Basisausbildung erfolgreich zu bewältigen: **{prob}%**")
        
        # Farbe des Fortschrittsbalkens je nach Eignung
        bar_color = "green" if prob >= 70 else "orange" if prob >= 40 else "red"
        st.progress(prob / 100.0)
        
        if prob < 40:
            st.warning("⚠️ Aufgrund der vorliegenden Daten wird eine Eignung aktuell als gering eingeschätzt.")
        elif prob < 70:
            st.info("ℹ️ Eine Eignung ist gegeben, aber es zeigen sich deutliche Entwicklungsfelder.")
        else:
            st.success("✅ Hohe Eignung für die Extrembelastungen der SEK-Ausbildung.")
            
        # Gegenüberstellung der integrierten Daten
        st.divider()
        st.subheader("Verrechnete Informationen aus der diagnostischen Black Box:")
        
        # Layout angepasst auf 4 Spalten
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(label="Logik-Score", value=f"{st.session_state.cognitive_score}%")
            st.caption(v.get("begruendung_kognition", ""))
        with col2:
            st.metric(label="Abiturnote", value=f"{st.session_state.abi_score}")
            st.caption(v.get("begruendung_abinote", ""))
        with col3:
            st.metric(label="Selbstbericht Stress", value=f"{st.session_state.self_score} / 5")
            st.caption(v.get("begruendung_selbstbericht", ""))
        with col4:
            st.metric(label="Interviewdaten", value="Text-Muster")
            st.caption(v.get("begruendung_interview", ""))
            
        st.divider()
        if st.button("🔄 App zurücksetzen (Für den nächsten Bewerber)", use_container_width=True):
            reset_app()

if __name__ == "__main__":
    main()

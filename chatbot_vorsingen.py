import streamlit as st
from openai import OpenAI
import json
import requests

# --- CONFIG & RESET ---
def reset_app():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# --- MAIN APP ---
def main():
    st.set_page_config(page_title="KI-Urteilsbildung: SEK-Auswahlverfahren", page_icon="⚡", layout="centered")
    
    # Initialisierung der Zustände
    if "step" not in st.session_state:
        st.session_state.step = "cognitive_test"  # Startet mit dem kognitiven Computertest
        st.session_state.messages = []
        st.session_state.cognitive_score = 80      # Standardwert für Computertest-Punkte
        st.session_state.stress_score = 3         # Standardwert für Stressresistenz-Fragebogen

    # --- PHASE 1: KOGNITIVER VORTEST (Psychometrisch) ---
    if st.session_state.step == "cognitive_test":
        st.title("Schritt 1: Kognitiver Leistungstest (EDV) 💻")
        st.write("Bitte geben Sie das Ergebnis von Max Mustermann aus dem computergestützten Vortest ein (z.B. Logisches Denken, Konzentration unter Druck):")
        
        st.session_state.cognitive_score = st.number_input(
            "Erreichte Punktzahl (0 bis 100 Punkte):",
            min_value=0,
            max_value=100,
            value=75,
            step=1
        )
        
        if st.button("Weiter zum Persönlichkeitsfragebogen 🚀", use_container_width=True):
            st.session_state.step = "questionnaire"
            st.rerun()

    # --- PHASE 2: PERSÖNLICHKEITSFRAGEBOGEN (Psychometrisch) ---
    elif st.session_state.step == "questionnaire":
        st.title("Schritt 2: Persönlichkeits-Fragebogen 📝")
        st.subheader("Dimension: Emotionale Stabilität & Stressresistenz")
        st.write("Bitte geben Sie an, wie sehr Max Mustermann der folgenden Aussage zustimmt:")
        
        st.session_state.stress_score = st.select_slider(
            "„Auch in unvorhersehbaren, bedrohlichen Situationen bleibe ich ruhig und handele absolut fokussiert.“",
            options=[1, 2, 3, 4, 5],
            value=3,
            format_func=lambda x: {1: "1 - Trifft gar nicht zu", 2: "2", 3: "3", 4: "4", 5: "5 - Trifft voll und ganz zu"}[x]
        )
        
        if st.button("Weiter zum KI-Eignungsinterview 🎤", use_container_width=True):
            st.session_state.step = "chat"
            st.session_state.messages = [
                {
                    "role": "system", 
                    "content": "Du bist ein psychologischer Diagnostiker im Auswahlverfahren für ein polizeiliches Spezialeinsatzkommando (SEK). Du interviewst den Bewerber Max Mustermann zu seiner Frustrationstoleranz und seinem Verhalten in Extremsituationen. Stelle prägnante, direkte, fordernde Fragen. Halte dich kurz."
                },
                {
                    "role": "assistant", 
                    "content": "Willkommen im Interview, Herr Mustermann. Stellen Sie sich vor: Sie sind im Einsatz, seit 14 Stunden ohne Schlaf, Ihr Teampartner fällt aus und der Zugriffplan funktioniert nicht mehr. Wie reagieren Sie in den ersten Sekunden?"
                }
            ]
            st.rerun()

    # --- PHASE 3: INTERVIEW CHAT (MAX 2 INTERAKTIONEN) ---
    elif st.session_state.step == "chat":
        st.title("Schritt 3: KI-gestütztes Eignungsinterview 💬")
        
        user_msgs_count = len([m for m in st.session_state.messages if m["role"] == "user"])
        st.progress(user_msgs_count / 2, text=f"Fortschritt: Frage {user_msgs_count} von 2")
        
        # Chat-Verlauf anzeigen
        for msg in st.session_state.messages:
            if msg["role"] != "system":
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

        # Logik für das Ende des Chats
        if user_msgs_count >= 2:
            st.success("Das strukturierte Kurz-Interview ist beendet.")
            if st.button("Automatisierte Datenverrechnung starten 📊", type="primary", use_container_width=True):
                st.session_state.step = "results"
                st.rerun()
        else:
            if prompt := st.chat_input("Antwort als Max Mustermann eingeben..."):
                st.session_state.messages.append({"role": "user", "content": prompt})
                
                if user_msgs_count == 0:
                    client = OpenAI(api_key=st.secrets["openai"]["api_key"])
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=st.session_state.messages
                    )
                    st.session_state.messages.append({"role": "assistant", "content": response.choices[0].message.content})
                
                st.rerun()

    # --- PHASE 4: AUTOMATISIERTE AUSWERTUNG (KI-URTEIL) ---
    elif st.session_state.step == "results":
        st.title("Schritt 4: Das Diagnostische KI-Urteil 🧠")
        
        if "ai_verdict" not in st.session_state:
            with st.spinner("Das KI-Modell verrechnet die multimethodalen Daten..."):
                try:
                    client = OpenAI(api_key=st.secrets["openai"]["api_key"])
                    chat_text = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages if m["role"] != "system"])
                    
                    prompt_integration = f"""
                    Du bist ein diagnostischer KI-Algorithmus zur automatisierten Verrechnung multimethodaler Daten für eine SEK-Auswahlentscheidung.
                    Dir liegen drei Datenquellen vor:
                    1. Kognitive Leistung (PC-Test, Skala 0-100 Punkte, höher ist besser): {st.session_state.cognitive_score} Punkte
                    2. Selbstbericht Stressresistenz (Skala 1-5, wobei 5 extrem stabil ist): {st.session_state.stress_score}
                    3. Transkript des KI-Eignungsinterviews:
                    {chat_text}
                    
                    Deine Aufgabe ist die mechanische/algorithmische Urteilsbildung. Schätze die Wahrscheinlichkeit (0-100%) ein, mit der Max Mustermann den nachfolgenden, extremen "Praxis-Härte-Parcours" der SEK-Ausbildung erfolgreich und ohne psychischen Abbruch bestehen wird.
                    Beachte: Für den SEK-Dienst ist die Kombination aus hoher Stressresistenz im Selbstbericht und besonnenen, taktischen Sprachmustern im Interview der stärkste Prädiktor.
                    
                    Gib die Antwort AUSSCHLIESSLICH als valides JSON-Objekt mit exakt diesen vier Keys aus:
                    "prognose_prozent": (Als Integer, z.B. 85),
                    "begruendung_pc_test": (Ein kurzer Satz, wie der kognitive Leistungswert einfließt),
                    "begruendung_selbstbericht": (Ein kurzer Satz, wie die angegebene Stressresistenz gewichtet wird),
                    "begruendung_interview": (Ein kurzer Satz, welches spezifische Antwortverhalten im Interview ausschlaggebend war)
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
                        "begruendung_pc_test": "Fehler bei der automatischen Auswertung",
                        "begruendung_selbstbericht": "Fehler", 
                        "begruendung_interview": "Fehler"
                    }

        # Visualisierung des Ergebnisses
        v = st.session_state.ai_verdict
        prob = v.get("prognose_prozent", 50)
        
        st.markdown(f"### Kriteriumsprognose für Max Mustermann:")
        st.markdown(f"#### Wahrscheinlichkeit, den Praxis-Härte-Parcours erfolgreich zu bestehen: **{prob}%**")
        st.progress(prob / 100.0)
        
        # Gegenüberstellung der integrierten Daten
        st.divider()
        st.subheader("Verrechnete Prädiktoren (Multimethodal):")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(label="Kognitiver PC-Test", value=f"{st.session_state.cognitive_score} / 100")
            st.caption(v.get("begruendung_pc_test", ""))
        with col2:
            st.metric(label="Stressresistenz", value=f"{st.session_state.stress_score} / 5")
            st.caption(v.get("begruendung_selbstbericht", ""))
        with col3:
            st.metric(label="Interview-Analyse", value="Text-Muster")
            st.caption(v.get("begruendung_interview", ""))
            
        st.divider()
        
        # Didaktischer Hinweis für die Präsentation
        st.info("💡 **Präsentations-Tipp:** Dieses KI-Urteil agiert als hochdimensionale, mechanische Datenverrechnung. Es demonstriert, wie unstrukturierte Interviewtexte zusammen mit psychometrischen Scores automatisiert zu einer Erfolgsprognose aggregiert werden.")
        
        if st.button("🔄 Nächsten Bewerber testen (Reset)", use_container_width=True):
            reset_app()

if __name__ == "__main__":
    main()

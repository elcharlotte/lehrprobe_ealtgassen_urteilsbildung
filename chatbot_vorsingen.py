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

# --- MAIN APP ---
def main():
    st.set_page_config(page_title="SEK-Auswahl Diagnostik-Demo", page_icon="👮‍♂️", layout="centered")
    
    # Initialisierung der Zustände
    if "step" not in st.session_state:
        st.session_state.step = "abi_grade"  # Startet direkt mit der Abiturnote
        st.session_state.messages = []
        st.session_state.abi_score = 2.0      # Standardwert für Abi-Note
        st.session_state.self_score = 3       # Standardwert für Fragebogen

    # --- PHASE 1: ABITURNOTE ---
    if st.session_state.step == "abi_grade":
        st.title("Schritt 1: Schulische Leistung (Abiturnote) 🎓")
        st.write("Bitte geben Sie Ihre Abschlussnote des Abiturs an:")
        # st.info("Hinweis: Eine gute Abiturnote korreliert oft mit kognitiver Grundfähigkeit, aber für SEK-Einsätze sind andere Faktoren meist ausschlaggebender.")
        
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

    # --- PHASE 2: FRAGEBOGEN (1 ITEM) ---
    elif st.session_state.step == "questionnaire":
        st.title("Schritt 2: Persönlichkeits-Fragebogen 🛡️")
        st.write("Bitte geben Sie an, wie sehr Sie der folgenden Aussage zustimmen:")
        
        st.session_state.self_score = st.select_slider(
            "Ich behalte auch in extrem stressigen Situationen einen kühlen Kopf und handle besonnen.",
            options=[1, 2, 3, 4, 5],
            value=3,
            format_func=lambda x: {1: "1 - Gar nicht stressresistent", 2: "2", 3: "3", 4: "4", 5: "5 - Sehr stressresistent"}[x]
        )
        
        if st.button("Weiter zum Kurz-Interview 🎤", use_container_width=True):
            st.session_state.step = "chat"
            # Das System-Setting und die erste (und einzige) Frage werden gesetzt
            st.session_state.messages = [
                {
                    "role": "system", 
                    "content": "Du bist ein psychologischer Diagnostiker für eine Polizeispezialeinheit (SEK). Du interviewst einen Bewerber kurz zum Thema Stressresistenz unter Extrembedingungen. Halte dich extrem kurz."
                },
                {
                    "role": "assistant", 
                    "content": "Erzählen Sie mir kurz von einer realen Situation, in der Sie physisch oder psychisch an Ihre absoluten Grenzen gestoßen sind. Wie genau haben Sie reagiert?"
                }
            ]
            st.rerun()

    # --- PHASE 3: SHORT CHAT (EXAKT 1 INTERAKTION) ---
    elif st.session_state.step == "chat":
        st.title("Schritt 3: Interview 💬")
        st.write("Bitte beantworten Sie die Frage des Diagnostikers:")
        
        # Zähle die echten User-Antworten
        user_msgs_count = len([m for m in st.session_state.messages if m["role"] == "user"])
        
        # Chat-Verlauf anzeigen
        for msg in st.session_state.messages:
            if msg["role"] != "system":
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

        # Wenn der User geantwortet hat, ist das Interview sofort beendet
        if user_msgs_count >= 1:
            st.success("Das Interview ist beendet. Ihre Antwort wurde aufgezeichnet.")
            if st.button("Mechanische Urteilsbildung starten 📊", type="primary", use_container_width=True):
                st.session_state.step = "results"
                st.rerun()
        else:
            if prompt := st.chat_input("Ihre Antwort eingeben..."):
                st.session_state.messages.append({"role": "user", "content": prompt})
                st.rerun()

    # --- PHASE 4: AUSWERTUNG & INTEGRATION ---
    elif st.session_state.step == "results":
        st.title("Schritt 4: Diagnostisches Urteil 🧠📊")
        
        if "ai_verdict" not in st.session_state:
            with st.spinner("Das LLM verrechnet die Daten..."):
                try:
                    client = OpenAI(api_key=st.secrets["openai"]["api_key"])
                    chat_text = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages if m["role"] != "system"])
                    
                    # Der Prompt verrechnet nun die 3 verbleibenden Datenquellen
                    prompt_integration = f"""
                    Du bist ein hochentwickelter diagnostischer Algorithmus zur Verrechnung multimethodaler Daten für das Auswahlverfahren einer Polizeispezialeinheit (SEK).
                    Dir liegen drei unterschiedliche Datenquellen vor:
                    1. Schulische Leistung (Abiturnote, wobei 1.0 am besten ist): {st.session_state.abi_score}
                    2. Selbstbericht Stressresistenz (Skala 1-5, wobei 5 extrem hoch ist): {st.session_state.self_score}
                    3. Das transkribierte Kurz-Interview (Nutzerantwort auf die Frage nach Grenzerfahrung):
                    {chat_text}
                    
                    Deine Aufgabe ist die mechanische Urteilsbildung (Prognose). Schätze die Wahrscheinlichkeit (0-100%) ein, mit der diese Person die **physischen und psychischen Extrembelastungen der SEK-Basisausbildung erfolgreich bewältigt**.
                    Beachte die Gewichtung: Für den SEK-Dienst sind psychische Stabilität und die im Interview gezeigte Reflexion/Verhalten in Krisen extrem wichtig. Die Abiturnote fließt als Indikator für kognitive Disziplin ein, wird aber gegenüber der Stressresistenz geringer gewichtet.
                    
                    Gib die Antwort AUSSCHLIESSLICH als valides JSON-Objekt mit exakt diesen vier Keys aus:
                    "prognose_prozent": (Als Integer, z.B. 75),
                    "begruendung_abinote": (Ein kurzer Satz, wie die Abiturnote einfließt),
                    "begruendung_selbstbericht": (Ein kurzer Satz, wie der Selbstbericht zur Stressresistenz einfließt),
                    "begruendung_interview": (Ein kurzer Satz, wie die Antwort im Interview bewertet wurde)
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
                        "begruendung_abinote": "Fehler bei der Berechnung",
                        "begruendung_selbstbericht": "Fehler", 
                        "begruendung_interview": "Fehler"
                    }

        # Visualisierung des Ergebnisses
        v = st.session_state.ai_verdict
        prob = v.get("prognose_prozent", 50)
        
        st.markdown(f"### Eignungsprognose:")
        st.markdown(f"#### Wahrscheinlichkeit, die SEK-Basisausbildung erfolgreich zu bewältigen: **{prob}%**")
        st.progress(prob / 100.0)
        
        if prob < 40:
            st.warning("⚠️ Geringe Eignung: Die Kombination aus den vorliegenden Daten deutet auf ein erhöhtes Risiko bei Extrembelastungen hin.")
        elif prob < 70:
            st.info("ℹ️ Bedingte Eignung: Grundvoraussetzungen sind erfüllt, es zeigen sich jedoch kritische Faktoren in der Stressbewältigung.")
        else:
            st.success("✅ Hohe Eignung: Das Profil zeigt eine überdurchschnittliche Passung für die psychischen Anforderungen der Spezialkräfte.")
            
        # Gegenüberstellung der integrierten Daten (Zurück auf 3 Spalten)
        st.divider()
        st.subheader("Verrechnete Informationen aus der diagnostischen Black Box:")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(label="Abiturnote", value=f"{st.session_state.abi_score}")
            st.caption(v.get("begruendung_abinote", ""))
        with col2:
            st.metric(label="Selbstbericht Stress", value=f"{st.session_state.self_score} / 5")
            st.caption(v.get("begruendung_selbstbericht", ""))
        with col3:
            st.metric(label="Interview-Antwort", value="Text-Muster")
            st.caption(v.get("begruendung_interview", ""))
            
        st.divider()
        if st.button("🔄 App zurücksetzen (Für den nächsten Bewerber)", use_container_width=True):
            reset_app()

if __name__ == "__main__":
    main()

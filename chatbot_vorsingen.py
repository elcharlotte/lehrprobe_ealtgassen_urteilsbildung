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
    st.set_page_config(page_title="KI-Urteilsbildung Live-Demo", page_icon="🧠", layout="centered")
    
    # Initialisierung
    if "step" not in st.session_state:
        st.session_state.step = "questionnaire"
        st.session_state.messages = []
        st.session_state.self_score = 3

    # --- PHASE 1: FRAGEBOGEN (1 ITEM) ---
    if st.session_state.step == "questionnaire":
        st.title("Schritt 1: Fragebogen 📝")
        st.write("Bitte geben Sie an, wie sehr Sie der folgenden Aussage zustimmen:")
        
        st.session_state.self_score = st.select_slider(
            "Ich erledige Aufgaben stets gründlich und schiebe sie selten auf.",
            options=[1, 2, 3, 4, 5],
            value=3,
            format_func=lambda x: {1: "1 - Gar nicht", 2: "2", 3: "3", 4: "4", 5: "5 - Voll und ganz"}[x]
        )
        
        if st.button("Weiter zum Kurz-Interview 🚀", use_container_width=True):
            st.session_state.step = "chat"
            st.session_state.messages = [
                {
                    "role": "system", 
                    "content": "Du bist ein psychologischer Diagnostiker. Du interviewst die Person kurz zum Thema Gewissenhaftigkeit und Zuverlässigkeit. Stelle prägnante, direkte Fragen. Halte dich kurz."
                },
                {
                    "role": "assistant", 
                    "content": "Willkommen zum Mini-Interview. Erzählen Sie mir kurz: Gab es in der letzten Zeit eine Situation, in der Sie eine wichtige Deadline fast verpasst hätten? Wie haben Sie reagiert?"
                }
            ]
            st.rerun()

    # --- PHASE 2: SHORT CHAT (MAX 2 INTERAKTIONEN) ---
    elif st.session_state.step == "chat":
        st.title("Schritt 2: Interview 💬")
        
        # Zähle die echten User-Antworten
        user_msgs_count = len([m for m in st.session_state.messages if m["role"] == "user"])
        st.progress(user_msgs_count / 2, text=f"Fortschritt: Frage {user_msgs_count} von 2")
        
        # Chat-Verlauf anzeigen
        for msg in st.session_state.messages:
            if msg["role"] != "system":
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

        # Logik für das Ende des Chats
        if user_msgs_count >= 2:
            st.success("Das Interview ist beendet.")
            if st.button("Mechanische Urteilsbildung starten 📊", type="primary", use_container_width=True):
                st.session_state.step = "results"
                st.rerun()
        else:
            if prompt := st.chat_input("Ihre Antwort eingeben..."):
                st.session_state.messages.append({"role": "user", "content": prompt})
                
                # Wenn es die erste Antwort war, holt die KI die zweite Frage
                if user_msgs_count == 0:
                    client = OpenAI(api_key=st.secrets["openai"]["api_key"])
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=st.session_state.messages
                    )
                    st.session_state.messages.append({"role": "assistant", "content": response.choices[0].message.content})
                
                st.rerun()

    # --- PHASE 3: AUSWERTUNG & INTEGRATION ---
    elif st.session_state.step == "results":
        st.title("Schritt 3: Das Diagnostische Urteil 🧠")
        
        if "ai_verdict" not in st.session_state:
            with st.spinner("Das LLM verrechnet die Daten..."):
                try:
                    client = OpenAI(api_key=st.secrets["openai"]["api_key"])
                    chat_text = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages if m["role"] != "system"])
                    
                    prompt_integration = f"""
                    Du bist ein diagnostischer Algorithmus zur Verrechnung multimethodaler Daten.
                    Dir liegen zwei Datenquellen vor:
                    1. Selbstbericht (Skala 1-5, wobei 5 hoch gewissenhaft ist): {st.session_state.self_score}
                    2. Ein transkribiertes Kurz-Interview:
                    {chat_text}
                    
                    Deine Aufgabe ist die mechanische Urteilsbildung (Prognose). Schätze die Wahrscheinlichkeit (0-100%) ein, mit der diese Person einen überdurchschnittlichen Masterabschluss für das Fach Psychologie zu erwirbt.
                    
                    Gib die Antwort AUSSCHLIESSLICH als valides JSON-Objekt mit exakt diesen drei Keys aus:
                    "prognose_prozent": (Als Integer, z.B. 75),
                    "begruendung_selbstbericht": (Ein kurzer Satz, wie der Fragebogenwert einfließt),
                    "begruendung_interview": (Ein kurzer Satz, welches Sprachmuster im Interview ausschlaggebend war)
                    """
                    
                    res = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": prompt_integration}],
                        response_format={"type": "json_object"}
                    )
                    st.session_state.ai_verdict = json.loads(res.choices[0].message.content)
                except Exception as e:
                    st.error(f"Fehler bei der Berechnung: {e}")
                    st.session_state.ai_verdict = {"prognose_prozent": 50, "begruendung_selbstbericht": "Fehler", "begruendung_interview": "Fehler"}

        # Visualisierung des Ergebnisses
        v = st.session_state.ai_verdict
        prob = v.get("prognose_prozent", 50)
        
        st.markdown(f"### Kriteriumsprognose:")
        st.markdown(f"#### Wahrscheinlichkeit einen überdurchschnittlichen Masterabschluss zu absolvieren: **{prob}%**")
        st.progress(prob / 100.0)
        
        # Gegenüberstellung der integrierten Daten
        st.divider()
        st.subheader("Verrechnete Informationen aus der Black Box:")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric(label="Fragebogendaten", value=f"{st.session_state.self_score} / 5")
            st.caption(v.get("begruendung_selbstbericht", ""))
        with col2:
            st.metric(label="Interviewdaten", value="Text-Muster")
            st.caption(v.get("begruendung_interview", ""))
            
        st.divider()
        if st.button("🔄 App zurücksetzen (Für den nächsten Tester)", use_container_width=True):
            reset_app()

if __name__ == "__main__":
    main()

import streamlit as st
import random
import speech_recognition as sr
import sqlite3
from datetime import datetime
from google import genai  # 👈 New Free SDK

# ⚠️ 1. Set page config MUST be the first Streamlit command!
st.set_page_config(page_title="AI Interview Bot", layout="centered")

# ==========================================
# 🗄️ DATABASE CONNECTION & CREATION
# ==========================================
conn = sqlite3.connect("users.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS interview_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    score INTEGER,
    category TEXT,
    date TEXT
)
""")
conn.commit()

# ==========================================
# 🧠 MEMORY MANAGEMENT (Session State)
# ==========================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user" not in st.session_state:
    st.session_state.user = None

if "saved" not in st.session_state:
    st.session_state.saved = False

if "question_count" not in st.session_state:
    st.session_state.question_count = 0

if "total_score" not in st.session_state:
    st.session_state.total_score = 0

# 🔥 Store feedback & dynamic score dynamically so rerun doesn't wipe them
if "ai_feedback" not in st.session_state:
    st.session_state.ai_feedback = "Submit an answer to see AI insights."
if "current_score" not in st.session_state:
    st.session_state.current_score = 0

# ==========================================
# 🔐 AUTHENTICATION FUNCTION
# ==========================================
def login():
    st.title("🔐 Authentication")
    mode = st.radio("Select Action", ["Login", "Signup"], horizontal=True)
    username = st.text_input("Username", key="auth_user")
    password = st.text_input("Password", type="password", key="auth_pass")

    if mode == "Signup":
        if st.button("Create Account"):
            if username and password:
                c.execute("SELECT * FROM users WHERE username=?", (username,))
                if c.fetchone():
                    st.error("User already exists ❌")
                else:
                    c.execute("INSERT INTO users VALUES (?, ?)", (username, password))
                    conn.commit()
                    st.success("Account created successfully ✅ Go to Login!")
            else:
                st.warning("Please enter username and password! ⚠️")
    else:
        if st.button("Login"):
            c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
            if c.fetchone():
                st.session_state.logged_in = True
                st.session_state.user = username
                st.success("Login Successful ✅")
                st.rerun()
            else:
                st.error("Invalid Credentials ❌")

# ==========================================
# 🚀 MAIN APP FLOW CONTROL
# ==========================================
if not st.session_state.logged_in:
    login()
else:
    st.title("🎤 AI Interview Bot")
    st.write(f"Welcome **{st.session_state.user}** 👋")
    
    if st.button("Logout 🚪"):
        st.session_state.logged_in = False
        st.session_state.user = None
        st.rerun()

    st.markdown("---")

    # --- HISTORY TAB ---
    st.subheader("📊 My Interview History")
    c.execute(
        "SELECT score, category, date FROM interview_history WHERE username=? ORDER BY id DESC",
        (st.session_state.user,)
    )
    history = c.fetchall()

    if history:
        st.table(history)
        scores = [row[0] for row in history]
        st.line_chart(scores) 
    else:
        st.info("No history yet 📋 Start your first interview below!")

    st.markdown("---")

    # --- INTERVIEW FLOW ---
    category = st.selectbox("Select Interview Type", ["HR", "Technical"])
    
    if category == "HR":
        questions = [
            "Tell me about yourself",
            "Why should we hire you?",
            "What are your strengths?",
            "What are your weaknesses?"
        ]
    else:
        questions = [
            "What is Python?",
            "Explain Machine Learning",
            "What is SQL?",
            "Explain OOP concepts"
        ]
        
    if "prev_category" not in st.session_state:
        st.session_state.prev_category = category

    if st.session_state.prev_category != category:
        st.session_state.question = random.choice(questions)
        st.session_state.prev_category = category

    if "question" not in st.session_state:
        st.session_state.question = random.choice(questions)

    st.write(f"Question {st.session_state.question_count + 1} of 5")
    st.subheader("❓ Interview Question")
    st.write(st.session_state.question)

    answer = st.text_area("✍️ Your Answer:")
    
        if st.button("🎤 Use Voice Input"):
        st.warning("⚠️ Voice input not supported in deployed version")
        r = sr.Recognizer()  # Make sure 'r' is initialized inside the button click
        with sr.Microphone() as source:
            st.info("Speak now...")
            audio = r.listen(source)
            try:
                text = r.recognize_google(audio)
                st.success("You said: " + text)
                answer = text
            except Exception as e:
                st.error("Could not understand audio")


    # ==========================================
    # 🤖 NEW: REAL AI EVALUATION WITH GEMINI
    # ==========================================
    if st.button("Submit Answer"):
        if answer:
            with st.spinner("🤖 AI is analyzing your answer... Please wait..."):
                try:
                    # ⚠️ Paste your actual API key below inside quotes
                    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
                    
                    prompt = f"""
                    You are an expert tech and HR interviewer. Evaluate the candidate's answer for the given question.
                    
                    Question: "{st.session_state.question}"
                    Candidate Answer: "{answer}"
                    Interview Type: "{category}"
                    
                    Provide the response in the exact following format:
                    SCORE: [Give an integer score out of 10 based on accuracy, e.g., 7]
                    FEEDBACK: [Provide a constructive 2-3 line feedback with strengths and improvement points]
                    """
                    
                    response = client.models.generate_content(
                        model='gemini-1.5-flash',
                        contents=prompt,
                    )
                    
                    response_text = response.text
                    
                    # Simple parsing to separate Score and Feedback
                    if "SCORE:" in response_text and "FEEDBACK:" in response_text:
                        parts = response_text.split("FEEDBACK:")
                        score_part = parts[0].replace("SCORE:", "").strip()
                        feedback_part = parts[1].strip()
                        
                        # Extract integer out of score_part securely
                        extracted_score = int(''.join(filter(str.isdigit, score_part)))
                    else:
                        extracted_score = 5
                        feedback_part = response_text
                        
                    st.session_state.current_score = extracted_score
                    st.session_state.ai_feedback = feedback_part
                    
                    # Update global scores
                    st.session_state.total_score += extracted_score
                    st.session_state.question_count += 1
                    st.success("Answer Evaluated by Real AI! ✅ Click 'Next Question'")
                    
                except Exception as e:
                    st.error(f"Gemini API Error: {e}")

    # Display Dynamic AI evaluation updates on UI
    st.markdown("---")
    st.subheader("📊 Real-Time AI Review")
    st.metric(label="Last Answer Score", value=f"{st.session_state.current_score} / 10")
    st.info(st.session_state.ai_feedback)
        
    # Navigation
    if st.button("Next Question") and st.session_state.question_count < 5:
        st.session_state.question = random.choice(questions)
        st.session_state.ai_feedback = "Submit an answer to see AI insights."
        st.session_state.current_score = 0
        st.rerun()
        
    # --- END SCREEN GENERATOR ---
    if st.session_state.question_count >= 5:
        if not st.session_state.saved:
            c.execute(
                "INSERT INTO interview_history (username, score, category, date) VALUES (?, ?, ?, ?)",
                (
                    st.session_state.user,
                    st.session_state.total_score,
                    category,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                )
            )
            conn.commit()
            st.session_state.saved = True
            st.success("Results saved to history permanently! 💾")

        st.subheader("🏁 Final Interview Result")
        st.write(f"Total Cumulative Score: {st.session_state.total_score} / 50")

        if st.session_state.total_score > 35:
            st.success("🔥 Excellent performance!")
        elif st.session_state.total_score > 20:
            st.info("👍 Good, but can improve")
        else:
            st.warning("⚠️ Needs improvement")

        report = f"Interview Report\n\nTotal Score: {st.session_state.total_score}/50\nQuestions Answered: {st.session_state.question_count}\nPerformance: "
        if st.session_state.total_score > 35:
            report += "Excellent"
        elif st.session_state.total_score > 20:
            report += "Good"
        else:
            report += "Needs Improvement"

        st.download_button(
            "📥 Download Report",
            report,
            file_name="interview_report.txt"
        )

        if st.button("Restart Interview", key="restart_btn"):
            st.session_state.saved = False
            st.session_state.question_count = 0
            st.session_state.total_score = 0
            st.session_state.current_score = 0
            st.session_state.ai_feedback = "Submit an answer to see AI insights."
            st.session_state.question = random.choice(questions)
            st.rerun()

    # Debug block helper
    st.markdown("---")
    if st.session_state.user == "admin":
       st.subheader("👥 All Users")
    c.execute("SELECT username FROM users")
    users = c.fetchall()
    st.table(users)

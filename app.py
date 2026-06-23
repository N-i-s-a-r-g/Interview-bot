import streamlit as st
import random
import speech_recognition as sr
import sqlite3
from datetime import datetime

# DB connect
conn = sqlite3.connect("users.db", check_same_thread=False)
c = conn.cursor()

# Create users table
c.execute("""
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password TEXT
)
""")

# Create interview history table
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

# ⚠️ 1. Set page config MUST be the first Streamlit command!
st.set_page_config(page_title="AI Interview Bot", layout="centered")

# Dummy user database
users = {
    "nisarg": "1234",
    "admin": "admin"
}

# Session init
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


# LOGIN FUNCTION
def login():
    st.title("🔐 Authentication")

    mode = st.radio("Select", ["Login", "Signup"])

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    # 🔥 SIGNUP
    if mode == "Signup":
        if st.button("Create Account"):
            c.execute("SELECT * FROM users WHERE username=?", (username,))
            if c.fetchone():
                st.error("User already exists ❌")
            else:
                c.execute("INSERT INTO users VALUES (?, ?)", (username, password))
                conn.commit()
                st.success("Account created ✅")

    # 🔥 LOGIN
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


# MAIN APP FLOW
if not st.session_state.logged_in:
    login()

else:
    st.title("🎤 AI Interview Bot")
    st.write(f"Welcome {st.session_state.user} 👋")
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
    st.info("No history yet")


# 🔥 OUTSIDE if-else
st.subheader("👥 All Users (Debug)")
c.execute("SELECT username FROM users")
users = c.fetchall()
st.table(users)
    # Logout
if st.button("Logout"):
   st.session_state.logged_in = False
   st.rerun()

   st.markdown("---")

    category = st.selectbox("Select Interview Type", ["HR", "Technical"])
    
    # Question bank
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

    # Session state for question tracking
    if "question" not in st.session_state:
        st.session_state.question = random.choice(questions)

    # Show question
    st.write(f"Question {st.session_state.question_count + 1} of 5")
    st.subheader("❓ Interview Question")
    st.write(st.session_state.question)

    # User answer
    answer = st.text_area("✍️ Your Answer:")
    
    if st.button("🎤 Use Voice Input"):
        r = sr.Recognizer()
        with sr.Microphone() as source:
            st.info("Speak now...")
            audio = r.listen(source)
            try:
                text = r.recognize_google(audio)
                st.success("You said: " + text)
                answer = text
            except:
                st.error("Could not understand audio")

    # Submit
    if st.button("Submit Answer"):
        if answer:
            feedback = ""
            score = 0

# MAIN APP FLOW
if not st.session_state.logged_in:
    login()

else:
    # ===============================
    # MAIN HEADER
    # ===============================
    st.title("🎤 AI Interview Bot")
    st.write(f"Welcome {st.session_state.user} 👋")

    # ===============================
    # 📊 USER HISTORY
    # ===============================
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
        st.info("No history yet")

    # ===============================
    # 👥 ALL USERS (DEBUG)
    # ===============================
    st.subheader("👥 All Users (Debug)")
    c.execute("SELECT username FROM users")
    users = c.fetchall()
    st.table(users)

    # ===============================
    # 🚪 LOGOUT
    # ===============================
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

    st.markdown("---")

    # ===============================
    # 🎯 CATEGORY
    # ===============================
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

    # ===============================
    # SESSION STATE
    # ===============================
    if "prev_category" not in st.session_state:
        st.session_state.prev_category = category

    if st.session_state.prev_category != category:
        st.session_state.question = random.choice(questions)
        st.session_state.prev_category = category

    if "question" not in st.session_state:
        st.session_state.question = random.choice(questions)

    # ===============================
    # QUESTION DISPLAY
    # ===============================
    st.write(f"Question {st.session_state.question_count + 1} of 5")
    st.subheader("❓ Interview Question")
    st.write(st.session_state.question)

    answer = st.text_area("✍️ Your Answer:")

    # ===============================
    # 🎤 VOICE INPUT
    # ===============================
    if st.button("🎤 Use Voice Input"):
        r = sr.Recognizer()
        with sr.Microphone() as source:
            st.info("Speak now...")
            audio = r.listen(source)
            try:
                text = r.recognize_google(audio)
                st.success("You said: " + text)
                answer = text
            except:
                st.error("Could not understand audio")

    # ===============================
    # SUBMIT ANSWER
    # ===============================
    if st.button("Submit Answer"):
        if answer:
            feedback = ""
            score = 0

            if len(answer) > 50:
                score += 5
                feedback += "✅ Good detailed answer\n"
            else:
                feedback += "⚠️ Answer too short\n"

            if "project" in answer.lower():
                score += 3
                feedback += "✅ Mentioned project\n"

            if "experience" in answer.lower():
                score += 2
                feedback += "✅ Mentioned experience\n"

            st.subheader("📊 Feedback")
            st.write(feedback)

            st.subheader("⭐ Score")
            st.write(f"{score} / 10")

            st.session_state.total_score += score
            st.session_state.question_count += 1

    # ===============================
    # 🤖 AI FEEDBACK
    # ===============================
    st.subheader("🤖 AI Feedback")

    if len(answer.split()) > 30:
        st.success("Strong answer with good explanation")
    elif len(answer.split()) > 15:
        st.info("Decent answer, try adding more details")
    else:
        st.warning("Answer is too short, elaborate more")

    if "project" not in answer.lower():
        st.write("👉 Try mentioning a project")

    if "because" not in answer.lower():
        st.write("👉 Add reasoning using 'because'")

    if "example" not in answer.lower():
        st.write("👉 Add an example for clarity")

    # ===============================
    # NEXT QUESTION
    # ===============================
    if st.button("Next Question") and st.session_state.question_count < 5:
        st.session_state.question = random.choice(questions)
        st.rerun()

    # ===============================
    # FINAL RESULT
    # ===============================
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

        st.subheader("🏁 Final Interview Result")
        st.write(f"Total Score: {st.session_state.total_score} / 50")

        if st.session_state.total_score > 35:
            st.success("🔥 Excellent performance!")
        elif st.session_state.total_score > 20:
            st.info("👍 Good, but can improve")
        else:
            st.warning("⚠️ Needs improvement")

        report = f"""
Interview Report

Score: {st.session_state.total_score}/50
Questions: {st.session_state.question_count}
"""

        st.download_button("📥 Download Report", report)

        if st.button("Restart Interview"):
            st.session_state.saved = False
            st.session_state.question_count = 0
            st.session_state.total_score = 0
            st.session_state.question = random.choice(questions)
            st.rerun()

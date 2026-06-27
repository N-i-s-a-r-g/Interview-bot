import streamlit as st
import random
import speech_recognition as sr
import sqlite3
from datetime import datetime
from google import genai 
import hashlib
import time

# ⚠️ 1. Set page config MUST be the first Streamlit command!
st.set_page_config(page_title="AI Interview Bot", layout="centered")

st.markdown("""
<style>
/* 🌈 Animated Gradient Background */
body {
    background: linear-gradient(-45deg, #020617, #0f172a, #0ea5e9, #1d4ed8);
    background-size: 400% 400%;
    animation: gradientBG 10s ease infinite;
}

@keyframes gradientBG {
    0% {background-position: 0% 50%;}
    50% {background-position: 100% 50%;}
    100% {background-position: 0% 50%;}
}

/* 🧊 Glass Effect Main Container */
.block-container {
    background: rgba(15, 23, 42, 0.65);
    backdrop-filter: blur(15px);
    border-radius: 20px;
    padding: 2rem;
    border: 1px solid rgba(255,255,255,0.1);
}

/* 🔐 Input Fields */
.stTextInput input, .stTextArea textarea {
    background-color: #1e293b;
    color: white;
    border-radius: 10px;
    border: 1px solid #334155;
    padding: 10px;
}

.stTextInput input:focus, .stTextArea textarea:focus {
    border: 1px solid #3b82f6;
    box-shadow: 0 0 10px #3b82f6;
}

/* 🎯 Buttons */
.stButton>button {
    background: linear-gradient(135deg, #3b82f6, #6366f1);
    color: white;
    border-radius: 12px;
    padding: 10px 20px;
    border: none;
    transition: all 0.3s ease;
}

.stButton>button:hover {
    transform: translateY(-3px) scale(1.05);
    background: linear-gradient(135deg, #2563eb, #4f46e5);
    box-shadow: 0 8px 25px rgba(99,102,241,0.7);
}

.stTable {
    background-color: #1e293b;
    border-radius: 10px;
}

.stAlert {
    border-radius: 12px;
}

h1, h2, h3 {
    color: #f8fafc;
    text-align: center;
}

hr {
    border: 1px solid #334155;
}
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 🗄️ SECTION 1: DATABASE CONNECTION & SCHEMA SETUP
# ==============================================================================
conn = sqlite3.connect("users.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password TEXT
)
""")

# UPGRADE 3: Added raw_answers and ai_review columns to map user details properly
c.execute("""
CREATE TABLE IF NOT EXISTS interview_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    score INTEGER,
    category TEXT,
    date TEXT,
    raw_answers TEXT,
    ai_review TEXT
)
""")
conn.commit()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ==============================================================================
# 🧠 SECTION 2: MEMORY MANAGEMENT (Session State Initialization)
# ==============================================================================
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

if "ai_feedback" not in st.session_state:
    st.session_state.ai_feedback = "Submit an answer to see AI insights."

if "current_score" not in st.session_state:
    st.session_state.current_score = 0

# UPGRADE 3: Cache current session full logs to save at the end
if "session_answers" not in st.session_state:
    st.session_state.session_answers = []

if "session_reviews" not in st.session_state:
    st.session_state.session_reviews = []

if "otp" not in st.session_state:
    st.session_state.otp = None

if "otp_user" not in st.session_state:
    st.session_state.otp_user = None

# ==============================================================================
# 🔐 SECTION 3: AUTHENTICATION FLOW
# ==============================================================================
def login():
    st.title("🔐 Authentication")
    mode = st.radio("Select Action", ["Login", "Signup", "Forgot Password"], horizontal=True)
    
    username = st.text_input("Username", key="auth_user")
    password = st.text_input("Password", type="password", key="auth_pass")

    if mode == "Signup":
        if st.button("Create Account"):
            if username and password:
                c.execute("SELECT * FROM users WHERE username=?", (username,))
                if c.fetchone():
                    st.error("User already exists ❌")
                else:
                    hashed = hash_password(password)
                    c.execute("INSERT INTO users VALUES (?, ?)", (username, hashed))
                    conn.commit()
                    st.success("Account created successfully ✅ Go to Login!")
            else:
                st.warning("Please enter username and password! ⚠️")
                
    elif mode == "Forgot Password":
        st.subheader("🔑 Reset Password with OTP")
        if st.button("Send OTP"):
            if username:
                c.execute("SELECT * FROM users WHERE username=?", (username,))
                if c.fetchone():
                    otp = random.randint(1000, 9999)   
                    st.session_state.otp = str(otp)    
                    st.session_state.otp_user = username
                    st.success(f"OTP: {otp} (demo only)")  
                else:
                    st.error("User not found ❌")
            else:
                st.warning("Enter your username above first! ⚠️")
                
        entered_otp = st.text_input("Enter OTP")
        new_password = st.text_input("New Password", type="password")

        if st.button("Verify & Reset"):
            if st.session_state.otp and entered_otp == st.session_state.otp:
                hashed = hash_password(new_password)
                c.execute("UPDATE users SET password=? WHERE username=?", (hashed, st.session_state.otp_user))
                conn.commit()
                st.success("Password reset successful ✅ You can log in now!")
                st.session_state.otp = None
                st.session_state.otp_user = None
            else:
                st.error("Invalid OTP or session expired ❌")
                
    else:
        if st.button("Login"):
            hashed = hash_password(password)
            c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, hashed))
            if c.fetchone():
                st.session_state.logged_in = True
                st.session_state.user = username
                st.success("Login Successful ✅")
                st.rerun()
            else:
                st.error("Invalid Credentials ❌")

# ==============================================================================
# 🚀 SECTION 4: CORE APPLICATION FLOW
# ==============================================================================
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

    # ==============================================================================
    # 📊 UPGRADE 1: USER HISTORY & ANALYTICS DASHBOARD
    # ==============================================================================
    st.subheader("📊 My Performance Dashboard")
    c.execute("SELECT score, category, date FROM interview_history WHERE username=? ORDER BY id DESC", (st.session_state.user,))
    history = c.fetchall()

    if history:
        total_interviews = len(history)
        scores_list = [row[0] for row in history]
        avg_score = sum(scores_list) / total_interviews
        best_score = max(scores_list)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(label="Total Interviews 🏁", value=total_interviews)
        with col2:
            st.metric(label="Average Score 📈", value=f"{avg_score:.1f} / 50")
        with col3:
            st.metric(label="Personal Best ⭐", value=best_score)
            
        st.markdown("### 📉 Historical Score Progress Trend")
        st.line_chart(scores_list)
        
        with st.expander("📄 View Full Detailed Logs (Answers & Reviews)"):
            c.execute("SELECT score, category, date, raw_answers, ai_review FROM interview_history WHERE username=? ORDER BY id DESC", (st.session_state.user,))
            full_history = c.fetchall()
            for row in full_history:
                st.write(f"**Date:** {row[2]} | **Category:** {row[1]} | **Total Score:** {row[0]}/50")
                st.info(f"💬 **AI Review Log:**\n{row[4]}")
                st.markdown("---")
    else:
        st.info("No history logs yet 📋 Complete an interview sequence to activate your analytics dashboard!")

    st.markdown("---")

    # 🎤 SUB-SECTION: LIVE INTERVIEW FLOW RUNNER
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

    # ==============================================================================
    # ⏱️ UPGRADE 2: INTERVIEW QUESTION TIMER (SAFE NON-BLOCKING FIXED VERSION)
    # ==============================================================================
    if "start_time" not in st.session_state or st.session_state.get("last_q") != st.session_state.question:
        st.session_state.start_time = time.time()
        st.session_state.last_q = st.session_state.question

    elapsed_time = int(time.time() - st.session_state.start_time)
    remaining_time = max(0, 60 - elapsed_time)

    if remaining_time > 0:
        st.metric(label="⏳ Time Remaining for this question", value=f"{remaining_time} Seconds")
        if remaining_time < 15:
            st.warning("⚠️ Action window closing! Please finalize your thoughts and submit.")
    else:
        st.error("⏰ **Time's Up!** Please summarize your thoughts and click 'Submit Answer' immediately!")

    answer = st.text_area("✍️ Your Answer:", key=f"ans_{st.session_state.question_count}")
    
    # 🎙️ AUDIO CAPTURE SYSTEM
    if st.button("🎤 Use Voice Input"):
        st.warning("⚠️ Voice input not supported in deployed version")
        r = sr.Recognizer()  
        with sr.Microphone() as source:
            st.info("Speak now...")
            audio = r.listen(source)
            try:
                text = r.recognize_google(audio)
                st.success("You said: " + text)
                answer = text
            except Exception as e:
                st.error("Could not understand audio")

    # ==============================================================================
    # 🤖 UPGRADE 4: AI PROCESSING LAYER (DETAILED METRICS BREAKDOWN)
    # ==============================================================================
    if st.button("Submit Answer"):
        if answer:
            with st.spinner("🤖 AI is analyzing your answer... Please wait..."):
                try:
                    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
                    
                    prompt = f"""
                    You are an expert tech and HR interviewer. Evaluate the candidate's answer for the given question.
                    
                    Question: "{st.session_state.question}"
                    Candidate Answer: "{answer}"
                    Interview Type: "{category}"
                    
                    Provide the response in the exact following template format:
                    SCORE: [Give an integer score out of 10 based on accuracy]
                    STRENGTHS: [List 1-2 strengths of the answer]
                    WEAKNESSES: [List 1-2 gaps or missing points]
                    IMPROVEMENT TIPS: [Provide 1 actionable tip to make the answer better]
                    """
                    
                    response = client.models.generate_content(
                        model='gemini-1.5-flash',
                        contents=prompt,
                    )
                    
                    response_text = response.text
                    
                    # Secure integer extractor out of raw text response
                    extracted_score = 5
                    if "SCORE:" in response_text:
                        try:
                            score_part = response_text.split("SCORE:")[1].split("\n")[0]
                            extracted_score = int(''.join(filter(str.isdigit, score_part)))
                        except:
                            extracted_score = 5
                            
                    st.session_state.current_score = extracted_score
                    st.session_state.ai_feedback = response_text
                    
                    # UPGRADE 3: Cache current item details to session stack memory
                    st.session_state.session_answers.append(f"Q: {st.session_state.question} | A: {answer}")
                    st.session_state.session_reviews.append(f"Q: {st.session_state.question} | Review:\n{response_text}")
                    
                    st.session_state.total_score += extracted_score
                    st.session_state.question_count += 1
                    st.success("Answer Evaluated by Real AI! ✅ Click 'Next Question'")
                    
                except Exception as e:
                    st.error(f"Gemini API Error: {e}")

    # UI Feedback Presentation Rendering
    st.markdown("---")
    st.subheader("📊 Real-Time AI Review Breakdown")
    st.metric(label="Last Answer Score", value=f"{st.session_state.current_score} / 10")
    st.info(st.session_state.ai_feedback)
        
    # Navigation Matrix Control
    if st.button("Next Question") and st.session_state.question_count < 5:
        st.session_state.question = random.choice(questions)
        st.session_state.ai_feedback = "Submit an answer to see AI insights."
        st.session_state.current_score = 0
        st.rerun()
        
    # ==============================================================================
    # 🏁 UPGRADE 3 & 5: RESULTS LOG GENERATION & REPORT SETUP
    # ==============================================================================
    if st.session_state.question_count >= 5:
        if not st.session_state.saved:
            # Flatten answer stacks to string blocks permanently
            flat_answers = " || ".join(st.session_state.session_answers)
            flat_reviews = " || ".join(st.session_state.session_reviews)
            
            c.execute(
                "INSERT INTO interview_history (username, score, category, date, raw_answers, ai_review) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    st.session_state.user,
                    st.session_state.total_score,
                    category,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    flat_answers,
                    flat_reviews
                )
            )
            conn.commit()
            st.session_state.saved = True
            st.success("Full session logs successfully saved to your profile data history! 💾")

        st.subheader("🏁 Final Interview Result")
        st.write(f"Total Cumulative Score: {st.session_state.total_score} / 50")

        if st.session_state.total_score > 35:
            st.success("🔥 Excellent performance!")
        elif st.session_state.total_score > 20:
            st.info("👍 Good, but can improve")
        else:
            st.warning("⚠️ Needs improvement")

        report = f"Interview Report\n\nTotal Score: {st.session_state.total_score}/50\nPerformance: "
        if st.session_state.total_score > 35:
            report += "Excellent"
        elif st.session_state.total_score > 20:
            report += "Good"
        else:
            report += "Needs Improvement"
            
        report += "\n\n--- Detailed Log Breakdown ---\n" + "\n".join(st.session_state.session_reviews)

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
            st.session_state.session_answers = []
            st.session_state.session_reviews = []
            st.session_state.question = random.choice(questions)
            st.rerun()

    # Admin Control Panel Log Panel
    if st.session_state.user == "admin":
        st.markdown("---")
        st.subheader("👥 All Users (Admin Control Panel)")
        c.execute("SELECT username FROM users")
        all_registered_users = c.fetchall()
        st.table(all_registered_users)

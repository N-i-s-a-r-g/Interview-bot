import streamlit as st
import random
import speech_recognition as sr
import sqlite3
from datetime import datetime
from google import genai 
import hashlib

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

/* Animation */
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

/* Focus glow */
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

/* ✨ Hover Animation */
.stButton>button:hover {
    transform: translateY(-3px) scale(1.05);
    background: linear-gradient(135deg, #2563eb, #4f46e5);
    box-shadow: 0 8px 25px rgba(99,102,241,0.7);
}

/* 📊 Tables */
.stTable {
    background-color: #1e293b;
    border-radius: 10px;
}

/* 📢 Info Box */
.stAlert {
    border-radius: 12px;
}

/* 📝 Headings */
h1, h2, h3 {
    color: #f8fafc;
    text-align: center;
}

/* Divider */
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

# Password Security Hashing
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

if "otp" not in st.session_state:
    st.session_state.otp = None

if "otp_user" not in st.session_state:
    st.session_state.otp_user = None

# ==============================================================================
# 🔐 SECTION 3: AUTHENTICATION FLOW (Login, Signup & Forgot Password)
# ==============================================================================
def login():
    st.title("🔐 Authentication")
    mode = st.radio("Select Action", ["Login", "Signup", "Forgot Password"], horizontal=True)
    
    username = st.text_input("Username", key="auth_user")
    password = st.text_input("Password", type="password", key="auth_pass")

    # 📁 SUB-SECTION: SIGNUP MODE
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
                
    # 📁 SUB-SECTION: FORGOT PASSWORD MODE 
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
                c.execute(
                    "UPDATE users SET password=? WHERE username=?",
                    (hashed, st.session_state.otp_user)
                )
                conn.commit()
                st.success("Password reset successful ✅ You can log in now!")
                st.session_state.otp = None
                st.session_state.otp_user = None
            else:
                st.error("Invalid OTP or session expired ❌")
                
    # 📁 SUB-SECTION: LOGIN MODE
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
# 🚀 SECTION 4: CORE APPLICATION FLOW (Runs only after validation)
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
    # 📊 SUB-SECTION: USER HISTORY & ANALYTICS DASHBOARD (UPGRADE 1)
    # ==============================================================================
    st.subheader("📊 My Performance Dashboard")
    
    # Fetch historical data for the logged-in user
    c.execute( "SELECT score, category, date FROM interview_history WHERE username=? ORDER BY id DESC",(st.session_state.user,) )
    history = c.fetchall()

    if history:
        # Core Analytics Calculations
        total_interviews = len(history)
        scores_list = [row[0] for row in history]
        avg_score = sum(scores_list) / total_interviews
        best_score = max(scores_list)
        
        # 3-Column Layout Grid for Stats
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(label="Total Interviews 🏁", value=total_interviews)
        with col2:
            st.metric(label="Average Score 📈", value=f"{avg_score:.1f} / 50")
        with col3:
            st.metric(label="Personal Best ⭐", value=f"{best_score} / 50")
            
        st.markdown("### 📉 Historical Score Progress Trend")
        st.line_chart(scores_list)
        
        # Keep the detailed table clean inside an expander
        with st.expander("📄 View Full Raw Logs Table"):
            st.table(history)
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
    # ==============================================================================
    # ⏱️ SUB-SECTION: INTERVIEW QUESTION TIMER (UPGRADE 2 - STABLE RUNNING VERSION)
    # ==============================================================================
    import time

    # Initialize timestamp memory elements securely
    if "start_time" not in st.session_state or st.session_state.get("last_q") != st.session_state.question:
        st.session_state.start_time = time.time()
        st.session_state.last_q = st.session_state.question

    elapsed_time = int(time.time() - st.session_state.start_time)
    remaining_time = max(0, 60 - elapsed_time)

    # Static component allocation map object container
    timer_placeholder = st.empty()

    if remaining_time > 0:
        # Render tracking format container blocks elements grid alignment setup properties
        timer_placeholder.metric(label="⏳ Live Time Remaining", value=f"{remaining_time} seconds")
        # Check active state and sleep runtime loop ticker cleanly
        if remaining_time > 1:
            time.sleep(1)
            st.rerun()
    else:
        timer_placeholder.error("⏰ **Time's Up!** Please type your summary and click 'Submit Answer' immediately!")


    answer = st.text_area("✍️ Your Answer:")
    
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

    # 🤖 AI PROCESSING LAYER (GEMINI CALL)
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
                    
                    Provide the response in the exact following format:
                    SCORE: [Give an integer score out of 10 based on accuracy, e.g., 7]
                    FEEDBACK: [Provide a constructive 2-3 line feedback with strengths and improvement points]
                    """
                    
                    response = client.models.generate_content(
                        model='gemini-1.5-flash',
                        contents=prompt,
                    )
                    
                    response_text = response.text
                    
                    if "SCORE:" in response_text and "FEEDBACK:" in response_text:
                        parts = response_text.split("FEEDBACK:")
                        score_part = parts[0].replace("SCORE:", "").strip()
                        feedback_part = parts[1].strip()
                        extracted_score = int(''.join(filter(str.isdigit, score_part)))
                    else:
                        extracted_score = 5
                        feedback_part = response_text
                        
                    st.session_state.current_score = extracted_score
                    st.session_state.ai_feedback = feedback_part
                    
                    st.session_state.total_score += extracted_score
                    st.session_state.question_count += 1
                    st.success("Answer Evaluated by Real AI! ✅ Click 'Next Question'")
                    
                except Exception as e:
                    st.error(f"Gemini API Error: {e}")

    # UI Feedback Presentation Rendering
    st.markdown("---")
    st.subheader("📊 Real-Time AI Review")
    st.metric(label="Last Answer Score", value=f"{st.session_state.current_score} / 10")
    st.info(st.session_state.ai_feedback)
        
    # Navigation Matrix Control
    if st.button("Next Question") and st.session_state.question_count < 5:
        st.session_state.question = random.choice(questions)
        st.session_state.ai_feedback = "Submit an answer to see AI insights."
        st.session_state.current_score = 0
        st.rerun()
        
    # 🏁 SUB-SECTION: RESULTS & METRIC DOWNLOAD GENERATOR
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

    # 🛠️ SUB-SECTION: ADMIN PANEL LOG PANEL CONTROLS
    if st.session_state.user == "admin":
        st.markdown("---")
        st.subheader("👥 All Users (Admin Control Panel)")
        c.execute("SELECT username FROM users")
        all_registered_users = c.fetchall()
        st.table(all_registered_users)

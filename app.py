import streamlit as st
import random
import speech_recognition as sr
# Dummy user database (for now)
users = {
    "nisarg": "1234",
    "admin": "admin"
}

# Session state init
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# LOGIN FUNCTION
def login():
    st.title("🔐 Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username in users and users[username] == password:
            st.session_state.logged_in = True
            st.session_state.user = username
            st.success("Login Successful ✅")
            st.rerun()
        else:
            st.error("Invalid Credentials ❌")
            if not st.session_state.logged_in:
               login()
else:
    st.title("🎤 AI Interview Bot")
    st.write(f"Welcome {st.session_state.user} 👋")
    if st.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()
if "question_count" not in st.session_state:
    st.session_state.question_count = 0

if "total_score" not in st.session_state:
    st.session_state.total_score = 0
st.set_page_config(page_title="AI Interview Bot", layout="centered")

st.title("🎤 AI Interview Bot")
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


# Session state
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

        # 👉 NEW
        st.session_state.total_score += score
        st.session_state.question_count += 1
# AI-like feedback
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
# Next question
if st.button("Next Question") and st.session_state.question_count < 5:
    st.session_state.question = random.choice(questions)
if st.session_state.question_count == 5:
    st.subheader("🏁 Final Interview Result")

    st.write(f"Total Score: {st.session_state.total_score} / 50")

    if st.session_state.total_score > 35:
        st.success("🔥 Excellent performance!")
    elif st.session_state.total_score > 20:
        st.info("👍 Good, but can improve")
    else:
        st.warning("⚠️ Needs improvement")

    # 👉 REPORT
    report = f"""
Interview Report

Total Score: {st.session_state.total_score}/50
Questions Answered: {st.session_state.question_count}
"""

    if st.session_state.total_score > 35:
        report += "Performance: Excellent"
    elif st.session_state.total_score > 20:
        report += "Performance: Good"
    else:
        report += "Performance: Needs Improvement"

    # 👉 DOWNLOAD (FIXED INDENT)
    st.download_button(
        "📥 Download Report",
        report,
        file_name="interview_report.txt"
    )

    # 👉 RESTART
    if st.button("Restart Interview", key="restart_btn"):
        st.session_state.question_count = 0
        st.session_state.total_score = 0
        st.session_state.question = random.choice(questions)
        st.rerun()
report = f"""
Interview Report

Total Score: {st.session_state.total_score}/50
Questions Answered: {st.session_state.question_count}

Performance:
"""

if st.session_state.total_score > 35:
    report += "Excellent"
elif st.session_state.total_score > 20:
    report += "Good"
else:
    report += "Needs Improvement"
    

import streamlit as st
import random

st.set_page_config(page_title="AI Interview Bot", layout="centered")

st.title("🎤 AI Interview Bot")

# Question bank
questions = [
    "Tell me about yourself",
    "What are your strengths?",
    "What are your weaknesses?",
    "Why should we hire you?",
    "Explain a project you worked on",
    "What is Python?",
    "What is Machine Learning?",
    "Describe a challenging situation and how you handled it"
]

# Session state
if "question" not in st.session_state:
    st.session_state.question = random.choice(questions)

# Show question
st.subheader("❓ Interview Question")
st.write(st.session_state.question)

# User answer
answer = st.text_area("✍️ Your Answer:")

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

# Next question
if st.button("Next Question"):
    st.session_state.question = random.choice(questions)

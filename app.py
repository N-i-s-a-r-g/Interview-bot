import streamlit as st
import random
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

        # 👉 NEW
        st.session_state.total_score += score
        st.session_state.question_count += 1

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

    if st.button("Restart Interview"):
        st.session_state.question_count = 0
        st.session_state.total_score = 0
        st.session_state.question = random.choice(questions)

    if st.button("Restart Interview"):
        st.session_state.question_count = 0
        st.session_state.total_score = 0
        st.session_state.question = random.choice(questions)

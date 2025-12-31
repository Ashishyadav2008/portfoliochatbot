import streamlit as st
import json
import os
from datetime import datetime
from pathlib import Path
from openai import OpenAI

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Ashish Yadav | AI Portfolio Assistant",
    page_icon="🤖",
    layout="wide"
)

# ---------------- OPENAI CLIENT ----------------
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ---------------- PATHS ----------------
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
PORTFOLIO_FILE = DATA_DIR / "portfolio_knowledge.json"

# ---------------- LOAD PORTFOLIO ----------------
def load_portfolio():
    if not PORTFOLIO_FILE.exists():
        st.error("portfolio_knowledge.json not found")
        return {}
    with open(PORTFOLIO_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# ---------------- FORMAT SKILLS ----------------
def format_skills(skills_dict):
    lines = []
    for category, skills in skills_dict.items():
        lines.append(f"{category.replace('_',' ').title()}: {', '.join(skills)}")
    return "\n".join(lines)

# ---------------- SYSTEM PROMPT ----------------
def create_system_prompt(portfolio, selected_project=None):
    base_prompt = f"""
You are an AI Portfolio Assistant representing {portfolio.get('name')}.

Profile Summary:
{portfolio.get('summary')}

Education: {portfolio.get('education')}
Current Status: {portfolio.get('current_status')}
Career Goal: {portfolio.get('goal')}

Skills:
{format_skills(portfolio.get('skills', {}))}

Rules:
- Answer like a real interview candidate
- Be confident, clear, and honest
- Do NOT invent information
- Use simple English or Hinglish
"""

    if selected_project:
        base_prompt += f"""
Selected Project (Explain in detail):

Project Name: {selected_project.get('name')}
Type: {selected_project.get('type')}
Category: {selected_project.get('category')}

Problem:
{selected_project.get('problem')}

Solution:
{selected_project.get('solution')}

Tools Used:
{selected_project.get('tools')}

Outcome:
{selected_project.get('outcome')}

Instructions:
- Use STAR method if possible
- Explain business impact
- Answer follow-up technical questions
"""
    else:
        project_list = "\n".join(
            [f"- {p.get('name')} ({p.get('type')})" for p in portfolio.get("projects", [])]
        )
        base_prompt += f"""
Projects:
{project_list}

Instructions:
- Answer about skills, projects, resume, career goals
- Suggest selecting a project for deep explanation
"""
    return base_prompt

# ---------------- AI RESPONSE ----------------
def get_ai_response(user_message, chat_history, portfolio):
    selected_project = None

    if st.session_state.get("selected_project"):
        for p in portfolio.get("projects", []):
            if p.get("name") == st.session_state.selected_project:
                selected_project = p
                break

    messages = [{"role": "system", "content": create_system_prompt(portfolio, selected_project)}]

    for msg in chat_history:
        messages.append({"role": msg["role"], "content": msg["content"]})

    messages.append({"role": "user", "content": user_message})

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=messages,
        temperature=0.5,
        max_output_tokens=800
    )

    return response.output_text

# ---------------- MAIN APP ----------------
def main():
    st.title("🤖 Ashish Yadav – AI Portfolio Assistant")

    portfolio = load_portfolio()
    if not portfolio:
        return

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    if "selected_project" not in st.session_state:
        st.session_state.selected_project = None

    project_names = [p.get("name") for p in portfolio.get("projects", [])]

    selected = st.selectbox(
        "📂 Select a project for deep explanation (optional)",
        ["-- No Project Selected --"] + project_names
    )

    st.session_state.selected_project = None if selected == "-- No Project Selected --" else selected

    st.markdown("---")

    if not st.session_state.chat_history:
        st.info("👋 Ask about projects, skills, resume, or interview questions.")

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    user_input = st.chat_input("Ask your question...")

    if user_input:
        st.session_state.chat_history.append({
            "role": "user",
            "content": user_input,
            "time": datetime.now().isoformat()
        })

        reply = get_ai_response(
            user_input,
            st.session_state.chat_history[:-1],
            portfolio
        )

        st.session_state.chat_history.append({
            "role": "assistant",
            "content": reply,
            "time": datetime.now().isoformat()
        })

        st.rerun()

# ---------------- RUN ----------------
if __name__ == "__main__":
    main()

import streamlit as st
from src.ai_agent import SustainabilityAgent

st.title("🤖 Sustainability AI Chat Agent")

agent = SustainabilityAgent()

query = st.text_input("Ask your question in English:")

if st.button("Ask"):
    if query.strip():
        try:
            answer = agent.answer(query)
            st.write(answer)
        except Exception as e:
            st.error(str(e))

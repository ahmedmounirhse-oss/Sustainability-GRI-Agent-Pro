import streamlit as st
from pathlib import Path
from typing import Optional

# Import the unified agent
try:
    from src.ai_agent.agent import SustainabilityAgentPro
except Exception as e:
    st.error(f"Failed to import SustainabilityAgentPro: {e}")
    raise

# PAGE CONFIG
st.set_page_config(page_title="Chat Agent — Sustainability GRI", layout="wide")

st.title("💬 Chat Agent — Sustainability GRI")
st.write("Use the chat below to ask GRI-related questions or run a structured indicator analysis.")

# Create agent instance (singleton per session)
if "agent" not in st.session_state:
    st.session_state.agent = SustainabilityAgentPro()

agent: SustainabilityAgentPro = st.session_state.agent

# ----- SIDEBAR: Quick controls -----
with st.sidebar:
    st.header("Quick analysis")
    indicator = st.selectbox("Indicator (optional)", ["", "energy", "water", "emissions", "waste"], index=0)
    years = st.text_input("Years (comma separated, optional)", value="")
    run_struct = st.button("Run structured analysis")
    st.write("---")
    st.header("Chat settings")
    z_threshold = st.number_input("Anomaly z-threshold", min_value=1.0, max_value=6.0, value=3.0, step=0.5)
    st.write("\n")
    st.caption("Note: Files produced (CSV/PDF) are saved to the repo `output/` folder on the server.")

# ----- Main layout -----
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Ask a question or run an analysis")
    user_q = st.text_area(
        "Your question / command",
        placeholder="E.g. Show energy anomalies 2021 or How do I disclose GHG in GRI?",
        height=120
    )
    submit = st.button("Send")

    # Chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Free question
    if submit and user_q.strip():
        with st.spinner("Agent is thinking..."):
            query = user_q.strip()
            try:
                resp = agent.answer(query)
            except Exception as e:
                resp = f"Agent failed: {e}"

        st.session_state.chat_history.append((query, resp))

    # Structured analysis
    if run_struct:
        q_parts = []
        if indicator:
            q_parts.append(indicator)
        if years.strip():
            q_parts.append(years.strip())
        query = " ".join(q_parts) if q_parts else "show indicators"

        with st.spinner("Running structured analysis..."):
            try:
                resp = agent.answer(query)
            except Exception as e:
                resp = f"Agent failed: {e}"

        st.session_state.chat_history.append((query, resp))

    # Show chat history
    if st.session_state.chat_history:
        st.markdown("---")
        st.subheader("Conversation")
        for q, a in reversed(st.session_state.chat_history[-20:]):
            st.markdown(f"**User:** {q}")
            st.markdown(f"**Agent:** {a}")
            st.write("")

with col2:
    st.subheader("Latest Analysis / Artifacts")

    last = st.session_state.chat_history[-1] if st.session_state.chat_history else None

    if last:
        q, a = last
        st.markdown("**Last query:**")
        st.write(q)

        # 🔍 Try to extract file paths (CSV/PDF)
        lines = str(a).splitlines()
        paths = []

        for L in lines:
            if "output/" in L or "_analysis.csv" in L or "_summary.pdf" in L:
                s = L.strip()
                pos = s.find("output/")
                if pos != -1:
                    token = s[pos:].split()[0].strip(".,')\"")
                    paths.append(token)

        if paths:
            st.markdown("**Generated files**")
            for p in paths:
                pth = Path(p)
                if pth.exists():
                    st.write(f"- {p}")
                    try:
                        with open(pth, "rb") as fh:
                            st.download_button(
                                label=f"Download {pth.name}",
                                data=fh,
                                file_name=pth.name
                            )
                    except Exception as e:
                        st.write(f"Could not open {p}: {e}")
                else:
                    st.write(f"- {p} (not found on server)")

    else:
        st.write("Run an analysis or ask a question to see outputs here.")

# Footer
st.markdown("---")
st.caption("Tip: Put your indicator files inside the `data/` folder. Filenames should contain the indicator key (energy, water, emissions, waste).")

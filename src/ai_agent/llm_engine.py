import os
from typing import Any, Dict

from groq import Groq
from dotenv import load_dotenv

# Load .env variables
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise RuntimeError(
        "GROQ_API_KEY is not set. Please add it to your environment or .env file."
    )

client = Groq(api_key=GROQ_API_KEY)


def generate_sustainability_answer(question: str, kpi_context: Dict[str, Any]) -> str:
    """
    Main LLM interface to generate all sustainability-related answers.

    Smart behaviour:
    - If KPI context is provided → rely strictly on numbers inside context
    - If general question → answer using general GRI knowledge
    - If personal/meta question → introduce the AI agent
    """

    # ------------------- SYSTEM PROMPT -------------------
    system_prompt = """
You are a highly intelligent Sustainability & GRI Reporting AI Agent.

Your responsibilities:

1. **KPI-based questions** (when KPI context is provided):
   - Use ONLY the KPI numbers inside the context.
   - Never invent, estimate, or guess any new numerical values.
   - Provide GRI-compliant narrative, comparisons, trends, insights, or a forecast explanation.
   - Always be factual and analytical.

2. **General ESG/GRI questions** (e.g., “What is GRI?”, “Explain GRI 302”, 
   “What is materiality?”, “What is sustainability reporting?”):
   - Respond using your knowledge of sustainability and GRI standards.
   - Do NOT rely on KPI context.
   - Provide clear, concise, professional explanations.

3. **Personal or meta questions** (e.g., “Who are you?”, “What can you do?”):
   - Explain that you are an AI Sustainability Agent.
   - Clarify that you analyze KPIs, prepare GRI narratives, generate reports,
     and support ESG decision-making.

4. **Decision Logic**:
   - If the user question clearly relates to real numeric data → use KPI context.
   - If not → treat as a general GRI or meta question.

5. **Style Guidelines**:
   - Use clear, well-structured, professional English.
   - Avoid marketing language.
   - Use sustainability reporting tone suitable for GRI-aligned reports.

"""

    # Convert context to readable text
    context_text = f"KPI Context (raw data, do not modify numbers):\n{kpi_context}\n"

    # ------------------- MESSAGE BLOCK -------------------
    messages = [
        {
            "role": "system",
            "content": system_prompt.strip(),
        },
        {
            "role": "user",
            "content": (
                f"User question:\n{question}\n\n"
                f"{context_text}\n"
                "Produce the best possible answer based on the logic above."
            ),
        },
    ]

    # ------------------- LLM CALL -------------------
    completion = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=messages,
    temperature=0.2,
    max_tokens=800,
)


    return completion.choices[0].message.content.strip()

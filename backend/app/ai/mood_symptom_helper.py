import os
import json
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

llm = ChatOpenAI(openai_api_key=OPENAI_API_KEY, temperature=0.2, model="gpt-4o-mini")


def generate_pep_talk(mood_type: str = None, description: str = "", intensity: int = None) -> str:
    if mood_type:
        prompt = (
            f"The user is feeling {mood_type}."
            f"with an intensity level of {intensity}/10." if intensity else f"The user is feeling {mood_type}."
            f"{' Additional context: ' + description if description else ''}\n"
            f"Write a short encouraging pep talk directly addressing the user, that will make the user feel confident and motivated. "
            f"Remind the user that they already have everything within them needed to succeed, no matter what they are going through."
        )
    else:
        prompt = (
            f"{'Context: ' + description if description else 'The user is logging their mood.'}\n"
            f"Write a short encouraging pep talk directly addressing the user, that will make the user feel confident and motivated. "
            f"Remind the user that they already have everything within them needed to succeed, no matter what they are going through."
        )
    
    response = llm.invoke(prompt)
    # Try to extract the pep talk from the response
    text = response.content if hasattr(response, "content") else str(response)
    # If the model returns "Pep talk: ...", extract after the colon
    if "pep talk" in text.lower():
        return text.split(":", 1)[-1].strip()
    return text.strip()


def generate_affirmation(mood_type: str = None, description: str = "") -> str:
    if mood_type:
        prompt = (
            f"The user is feeling {mood_type}."
            f"{' Additional context: ' + description if description else ''}\n"
            f"Write a short positive, encouraging, optimistic, motivational and uplifting affirmation for the user."
        )
    else:
        prompt = (
            f"{'Context: ' + description if description else 'The user is logging their mood.'}\n"
            f"Write a short positive, encouraging, optimistic, motivational and uplifting affirmation for the user."
        )
    
    response = llm.invoke(prompt)
    # Try to extract the affirmation from the response
    text = response.content if hasattr(response, "content") else str(response)
    # If the model returns "Affirmation: ...", extract after the colon
    if "affirmation" in text.lower():
        return text.split(":", 1)[-1].strip()
    return text.strip()


def generate_symptom_advice(description: str) -> str:
    prompt = (
        f"The user reported following symptoms: '{description}'. "
        f"Provide short practical advice for the user to manage or cope with these symptoms."
    )
    response = llm.invoke(prompt)
    text = response.content if hasattr(response, "content") else str(response)
    # If the model returns "Advice: ...", extract after the colon
    if "advice" in text.lower():
        return text.split(":", 1)[-1].strip()
    return text.strip()


def generate_daily_quote() -> str:
    prompt = (
        "Generate a short, motivational, uplifting quote or affirmation that can inspire someone's day. "
        "Make it positive, encouraging, and universally applicable. "
        "Keep it concise (1-2 sentences maximum). "
        "Make it feel personal and direct to the reader."
    )
    
    response = llm.invoke(prompt)
    text = response.content if hasattr(response, "content") else str(response)
    return text.strip()

# def analyze_moods_and_symptoms(moods: list, symptoms: list, period: str = "the past month") -> str:
#     mood_summary = "\n".join([
#         f"{m['created_at']}: {m['mood_type']} (intensity {m['intensity']})"
#         f"{' - ' + m['description'] if m.get('description') else ''}"
#         for m in moods
#     ])
#     symptom_summary = "\n".join([f"{s['created_at']}: {s['description']} (intensity {s['intensity']})" for s in symptoms])
#     prompt = (
#         f"Analyze the following mood and symptom records for {period}.\n"
#         f"Moods:\n{mood_summary}\n"
#         f"Symptoms:\n{symptom_summary}\n"
#         f"Identify any patterns, trends, or correlations. Provide a summary and any helpful advice."
#     )
#     response = llm.invoke(prompt)
#     return response.content if hasattr(response, "content") else str(response)
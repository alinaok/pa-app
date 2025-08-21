# for LLM prompt templates and chains
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain


def mood_symptom_analysis_chain(llm):
    prompt = ChatPromptTemplate.from_template("""
You are a wellness analysis assistant.

User's mood and symptom history from {start_date} to {end_date}:

Moods:
{mood_data}

Symptoms:
{symptom_data}

Analyze the data and:
1. Identify patterns and trends in mood and symptoms.
2. Detect correlations between symptoms and mood states.
3. Suggest possible causes (e.g. work stress, sleep, diet).
4. Provide clear, practical advice.

Return in this JSON format:
{
  "patterns": "...",
  "correlations": "...",
  "possible_causes": "...",
  "recommendations": [
    "Try reducing caffeine after 3pm",
    "Establish a consistent sleep routine",
    "Practice breathing exercises when feeling anxious"
  ]
}
""")
    return LLMChain(llm=llm, prompt=prompt)




# # mood-only analysis
# def get_mood_analysis_chain(llm):
#     prompt = ChatPromptTemplate.from_template("""
# You are a compassionate mental wellness assistant.

# User's current mood:
# - Type: {current_mood}
# - Intensity: {intensity}
# - Description: {description}

# Recent mood entries:
# {mood_history}

# Your task:
# 1. Detect mood patterns from recent entries.
# 2. Suggest a possible cause for those patterns.
# 3. Offer personalized coping advice.
# 4. Generate a pep talk.
# 5. Provide a concise affirmation.

# Respond strictly in the following JSON format:

# {{
#   "mood_pattern": "...",
#   "possible_cause": "...",
#   "coping_advice": "...",
#   "pep_talk": "...",
#   "affirmation": "..."
# }}
# """)
#     return LLMChain(llm=llm, prompt=prompt)

# # symptom-only analysis
# def get_symptom_analysis_chain(llm):
#     prompt = ChatPromptTemplate.from_template("""
# You are a helpful health assistant.

# User's current symptom:
# - Description: {description}
# - Intensity: {intensity}

# Recent symptom entries:
# {symptom_history}

# Your task:
# 1. Detect if there's a recurring pattern.
# 2. Suggest a possible underlying cause.
# 3. Recommend at least one:
#    - Lifestyle adjustment
#    - Remedy or OTC treatment
#    - Supplement (if applicable)

# Return only structured JSON:

# {{
#   "symptom_pattern": "...",
#   "possible_cause": "...",
#   "recommendations": [
#     "Try drinking more water...",
#     "Use a warm compress...",
#     "Consider magnesium supplements..."
#   ]
# }}
# """)
#     return LLMChain(llm=llm, prompt=prompt)
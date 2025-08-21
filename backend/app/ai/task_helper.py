import os
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
import json 
from langchain.chains import LLMChain
from datetime import datetime
import pytz

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

llm = ChatOpenAI(openai_api_key=OPENAI_API_KEY, temperature=0.2, model="gpt-4o-mini")


def analyze_task_input(user_input: str, current_datetime: datetime = None) -> dict:
    """
    Analyzes user input to determine task timing, and scheduling details.
    
    Args:
        user_input: Natural language task description
        current_datetime: Current date and time (defaults to now in EST)
    """
    # Use current datetime or default to now in EST
    if current_datetime is None:
        est_tz = pytz.timezone('America/New_York')
        current_datetime = datetime.now(est_tz)
    
    # Format current datetime for the AI
    current_date_str = current_datetime.strftime("%Y-%m-%d")
    current_time_str = current_datetime.strftime("%H:%M")
    current_timezone = str(current_datetime.tzinfo)
    
    system_message = """You are a task analysis and task scheduling assistant. Your job is to convert user input into structured task metadata.

Your responsibilities:
1. Parse natural language task descriptions
2. Extract structured information for calendar scheduling
3. Estimate missing appropriate task durations and preferred times
4. Identify recurring patterns and end dates
5. Categorize tasks by type (work, personal, health)
6. Always return valid JSON format

Task categorization guidelines:
- Work: work related activities, meetings, deadlines, projects, tasks, tickets, etc.
- Personal: household chores, errands, personal appointments, personal growth activities, etc.
- Health: health related activities, medical appointments, medication, wellness activities.

Duration estimation guidelines:
- Quick tasks: 5-15 minutes (take pills, quick calls)
- Standard tasks: 30-60 minutes (laundry, cleaning, meetings)
- Complex tasks: 90-180 minutes (deep work, appointments)

IMPORTANT: You have access to the current date and time context. Use this to interpret relative dates like "today", "tomorrow", "next week", etc."""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_message),
        ("user", """Current context:
- Date: {current_date}
- Time: {current_time}
- Timezone: {current_timezone}

Analyze this task input: {user_input}

Return JSON with this structure:
{{
    "title": "Clear task title",
    "description": "Task description if provided",
    "due_date": "YYYY-MM-DD or null",
    "preferred_time": "HH:MM or null",
    "timezone": "timezone string (e.g., 'Asia/Bishkek', 'America/New_York') or null",
    "duration_minutes": number,
    "is_recurring": true/false,
    "recurrence_pattern": "daily|weekly|monthly or null",
    "recurrence_interval": number or null,
    "recurrence_end_date": "YYYY-MM-DD or null"
}}

Timezone guidelines:
- If user mentions a specific timezone (e.g., "Bishkek time", "EST", "PST"), extract it
- Use IANA timezone names (e.g., 'Asia/Bishkek', 'America/New_York', 'Europe/London')
- If no timezone mentioned, return null

Date interpretation guidelines:
- "today" means {current_date}
- "tomorrow" means the day after {current_date}
- "next week" means 7 days from {current_date}
- Day names (e.g., "monday", "tuesday", "sunday") should be interpreted as the NEXT occurrence of that day from {current_date}
- If today is Sunday and user says "sunday", schedule for next Sunday (7 days from today)
- If today is Monday and user says "sunday", schedule for this Sunday (6 days from today)
- Always convert relative dates to absolute YYYY-MM-DD format

Only return valid JSON, no additional text.""")
    ])
    
    chain = LLMChain(llm=llm, prompt=prompt)
    response = chain.invoke({
        "user_input": user_input,
        "current_date": current_date_str,
        "current_time": current_time_str,
        "current_timezone": current_timezone
    })
    
    try:
        # Handle different response formats
        if hasattr(response, 'content'):
            # Response is an AIMessage object
            content = response.content
        elif isinstance(response, dict):
            # Response is a dictionary
            content = response.get('text', str(response))
        else:
            # Response is something else, convert to string
            content = str(response)
        
        return json.loads(content)
    except (json.JSONDecodeError, AttributeError) as e:
        print(f"Error parsing AI response: {e}")
        print(f"Response type: {type(response)}")
        print(f"Response content: {response}")
        
        # Fallback parsing
        return {
            "title": user_input,
            "description": "",
            "due_date": None,
            "preferred_time": None,
            "timezone": None,
            "duration_minutes": 60,
            "is_recurring": False,
            "recurrence_pattern": None,
            "recurrence_interval": None,
            "recurrence_end_date": None
        }
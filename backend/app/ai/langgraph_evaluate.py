# orchestrates the workflow for evaluation (fetch, analyze, summarize)
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode
from app.ai.langchain_tools import get_mood_and_symptom_history
from app.ai.langchain_chains import mood_symptom_analysis_chain
from langchain_openai import ChatOpenAI
import json
from typing import TypedDict, List, Optional


llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.4)


class GraphState(TypedDict):
    user_id: str
    start_date: str
    end_date: str
    db: object
    mood_data: List[dict]
    symptom_data: List[dict]
    summary: dict
    error: Optional[str]


# Step 1: Fetch history
fetch_history = ToolNode(tools=[get_mood_and_symptom_history])

# Step 2: Run analysis
analysis_chain = mood_symptom_analysis_chain(llm)

def run_summary_analysis(state):
    try:
        inputs = {
            "start_date": state["start_date"],
            "end_date": state["end_date"],
            "mood_data": state["mood_data"],
            "symptom_data": state["symptom_data"]
        }
        result = analysis_chain.invoke(inputs)
        state["summary"] = json.loads(result)
    except Exception as e:
        state["error"] = str(e)
    return state

# Build graph
workflow = StateGraph(GraphState)
workflow.add_node("fetch_history", fetch_history)
workflow.add_node("analyze", run_summary_analysis)

workflow.set_entry_point("fetch_history")
workflow.add_edge("fetch_history", "analyze")
workflow.set_finish_point("analyze")

evaluate_graph = workflow.compile()

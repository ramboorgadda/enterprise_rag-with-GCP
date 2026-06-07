from typing import TypedDict,List,Annotated
import operator

class AgentState(TypedDict):
    """Represents the state of an agent, including its memory and any relevant metadata."""
    messages: Annotated[List[dict],operator.add]  # A list of memory entries (could be thoughts, observations, etc.)
    current_query: str
    documents: List[str]
    plan: List[str]
    status: str
    final_answer: str
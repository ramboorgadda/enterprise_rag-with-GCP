from langgraph.graph import StateGraph,END
from langgraph.checkpoint.memory import MemorySaver
from app.agents.state import AgentState
from app.agents.nodes.planner import planner_node
from app.agents.nodes.retriever import retrieve_node
from app.agents.nodes.responder import generate_node

#initialized workflow
workflow = StateGraph(AgentState)

# Added nodes to the langgraph workflow
workflow.add_node("planner", planner_node)
workflow.add_node("retriever", retrieve_node)
workflow.add_node("responder", generate_node)

# define edges and routing logic
def route_planner(state: AgentState):
    """ Routes the workflow based on the planner's decision."""
    
    if state["current_query"] == "CONVERSATIONAL":
        return "responder"
    else:
        return "retriever"
workflow.set_entry_point("planner")
#Adding conditional edges to the workflow
workflow.add_conditional_edges("planner", 
                            route_planner,
                                {
                                        "retriever": "retriever",
                                        "responder": "responder"
                                })
workflow.add_edge("retriever", "responder")
workflow.add_edge("responder", END)

# HYBRID MENORY UPGRADE

def get_checkpointer():
    """Returns a persistent Postgres checkpointer in Cloud/Production mode,
    and falls back to in-memory checkpointer in Local mode."""
    
    from app.config import settings
    if settings.LOCAL_MODE or not settings.DB_CONNECTION_NAME or not settings.DB_PASS:
        from langgraph.checkpoint.memory import MemorySaver
        print("⚠️ Running without Cloud SQL settings: Using in-memory checkpointer (no persistence).")
        return MemorySaver()
    try:
        from langgraph.checkpoint.postgres import PostgresSaver
        from psycopg_pool import ConnectionPool
        conninfo = f"postgresql://{settings.DB_USER}:{settings.DB_PASS}@/{settings.DB_NAME}?host=/cloudsql/{settings.DB_CONNECTION_NAME}"
        # Initialize the pool
        pool = ConnectionPool(conninfo=conninfo, max_size=5)
        
        with pool.connection() as conn:
            # Test the connection
            checkpointer = PostgresSaver(conn)
            checkpointer.setup()
        print("🐘 Using Persistent PostgresSaver (Cloud SQL Pool)")
        return PostgresSaver(pool)
    except Exception as e:
        print(f"⚠️ Failed to initialize PostgresSaver: {e}. Falling back to in-memory checkpointer.")
        from langgraph.checkpoint.memory import MemorySaver
        return MemorySaver()
# --- MEMORY UPGRADE ---
# MemorySaver allows the agent to remember conversations based on 'thread_id'
checkpointer = get_checkpointer()

# 4. Compile the Graph with Memory
rag_agent = workflow.compile(checkpointer=checkpointer)


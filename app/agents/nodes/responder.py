import logfire
from langchain_groq import ChatGroq
from app.agents.state import AgentState
from app.config import settings

llm = ChatGroq(model=settings.GROQ_MODEL, 
            api_key=settings.GROQ_API_KEY,
            temperature=0.1)

def generate_node(state: AgentState):
    """
    Synthesizes a response using both Documentation Context AND Conversation History.

    """
    query = state["current_query"]
    # Construct the prompt for GROQ based on the agent's state
    history=f""
    for msg in state["messages"][:-1]:
        role = "User" if msg["role"] == "user" else "Assistant"
        content = msg.get("content", "")
        history += f"{role}: {content}\n"
    user_message = state["messages"][-1]["content"] if state["messages"] else ""
    if query == "CONVERSATIONAL":
            logfire.info("Handling conversational query using memory only.")
            prompt = f"""
            You are a friendly and helpful Enterprise AI Assistant.
            Answer the user's latest message using the CONVERSATION HISTORY below.
        
            CONVERSATION HISTORY:
            {history}
        
            LATEST MESSAGE:
            "{user_message}"
            """
    else:
            logfire.info("Generating technical RAG response.")
            max_context_chars = 25000
            full_context = ""
            for doc in state["documents"]:
                if len(full_context) + len(doc["content"]) <= max_context_chars:
                    full_context += doc + "\n\n"
                else:
                    logfire.warning("Context truncated to fit Groq TPM limits.")
                    break
            prompt = f"""
        You are a Senior Technical Architect. 
        Answer the question using the TECHNICAL CONTEXT provided. 
        
        TECHNICAL CONTEXT:
        {full_context}
        
        CONVERSATION HISTORY:
        {history}
        
        USER QUESTION:
        "{user_message}"
        """
    with logfire.span("🧠 Generate Node - Synthesizing Response"):
        try:
            response = llm.invoke(prompt)
            logfire.info("Response generated successfully.")
            return {
                "finalanswer": response.content,
                "status:": "Response generated successfully.",
                "messages": [{"role": "assistant", "content": response.content}]
            }
        except Exception as e:
            logfire.error(f"Error during response generation: {e}")
            raise e
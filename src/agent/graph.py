from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.tools import tool

class State(TypedDict):
    messages: Annotated[list, add_messages]

@tool
def fetch_user_profile_data(config: dict) -> str:
    """Fetches user data, explicitly reading scoped info from the verified context."""
    # Step 3: Accessing security credentials directly from the agent runtime config
    auth_user = config.get("configurable", {}).get("langgraph_auth_user", {})
    user_id = auth_user.get("identity", "unknown_user")
    role = auth_user.get("user_role", "unknown_role")
    
    return f"Accessing account storage for User: {user_id} with verified access role: {role}."

# Simple agent loop node
async def call_agent(state: State, config: dict):
    # Execute tool securely using the runtime configuration context
    tool_output = await fetch_user_profile_data.ainvoke({}, config=config)
    return {"messages": [{"role": "assistant", "content": f"Tool says: {tool_output}"}]}

# Build Graph
workflow = StateGraph(State)
workflow.add_node("agent", call_agent)
workflow.add_edge(START, "agent")
workflow.add_edge("agent", END)

graph = workflow.compile()
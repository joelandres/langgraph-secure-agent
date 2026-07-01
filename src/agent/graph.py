# A common failure point in agent security is when the API layer knows who the user is,
# but the agent's internal nodes don't.

# LangGraph solves this by packing the verified user data into a special configuration object.
# Inside your nodes, you can pull the current user's scoped credentials straight out of the config.
# See fetch_user_profile_data tool below for an example of how to access the verified user context.
# See call_agent node below for an example of how to pass the config into a tool invocation.

from typing import Annotated
from typing_extensions import TypedDict
from langchain_core.runnables.config import var_child_runnable_config
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.tools import tool

class State(TypedDict):
    messages: Annotated[list, add_messages]

@tool
def fetch_user_profile_data() -> str:
    """Fetches user data, explicitly reading scoped info from the verified context."""
    # Accessing security credentials directly from the agent runtime config
    config = var_child_runnable_config.get() or {}
    auth_user = config.get("configurable", {}).get("langgraph_auth_user", {})
    user_id = auth_user.get("identity", "unknown_user")
    role = auth_user.get("user_role", "unknown_role")

    return f"Accessing account storage for User: {user_id} with verified access role: {role}."

# Simple agent loop node
async def call_agent(state: State):
    # Execute tool securely using the runtime configuration context
    tool_output = await fetch_user_profile_data.ainvoke({})
    return {"messages": [{"role": "assistant", "content": f"Tool says: {tool_output}"}]}

# Build Graph
workflow = StateGraph(State)
workflow.add_node("agent", call_agent)
workflow.add_edge(START, "agent")
workflow.add_edge("agent", END)

graph = workflow.compile()
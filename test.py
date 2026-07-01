# Securing the framework API handles only half the battle (see comments in auth.py and graph.py).
# Because LangGraph applications coordinate loops, tool calls, and data flows,
# you also need to harden the runtime environment:
# 
# Isolate Downstream Tool Credentials:
# Avoid giving the core LangGraph host unrestricted write access to database instances or system files.
# Treat tools as individual microservices requiring bounded permissions.
# 
# Sanitize Inputs Against Prompt Injections:
# If your graph pulls text dynamically from external vector stores, webpages, or user uploads,
# those strings can carry malicious instructions.
# 
# Treat all gathered text as untrusted data before passing it back into an LLM node.
# 
# To tie this all together, make sure your deployment configuration specifies your security routing.
# In your langgraph.json layout, point directly to your structured auth module.

import asyncio
import os
from dotenv import load_dotenv
from langgraph_sdk import get_client

# Load local .env first and allow it to override any shell environment variables.
load_dotenv(override=True)

LANGGRAPH_URL = os.getenv("LANGGRAPH_URL", "http://localhost:2024")

async def test_security_flow():
    # 1. Connect using Alice's Token
    alice_client = get_client(
        url=LANGGRAPH_URL,
        headers={"Authorization": "Bearer alice-secure-token"}
    )
    
    # Create a thread under Alice's account
    alice_thread = await alice_client.threads.create()
    print(f"Alice created thread: {alice_thread['thread_id']}")
    
    # Run the graph as Alice
    async for chunk in alice_client.runs.stream(
        thread_id=alice_thread["thread_id"],
        assistant_id="secure_agent",
        input={"messages": [{"role": "user", "content": "Run secure tool"}]}
    ):
        if chunk.event == "messages":
            print("Alice Stream:", chunk.data)

    # 2. Connect as Bob and try to see Alice's thread (Should fail / return empty)
    bob_client = get_client(
        url=LANGGRAPH_URL,
        headers={"Authorization": "Bearer bob-secure-token"}
    )
    
    # Try looking for Alice's specific thread via Bob's client
    try:
        visible_threads = await bob_client.threads.search()
        thread_ids = [t["thread_id"] for t in visible_threads]
        print(f"Bob sees these threads: {thread_ids}") # Will not show Alice's thread ID
    except Exception as e:
        print(f"Bob access rejected: {e}")

    # 3. Connect with an unlisted token (Should fail at the auth middleware with HTTP 401)
    intruder_client = get_client(
        url=LANGGRAPH_URL,
        headers={"Authorization": "Bearer invalid-token-xyz"}
    )

    # The request is blocked by get_current_user() in auth.py before reaching the graph
    try:
        await intruder_client.threads.create()
        print("SECURITY FAILURE: Invalid token was accepted!")
    except Exception as e:
        print(f"Invalid token rejected: {e}") # Expect HTTP 401: Unauthorized token

if __name__ == "__main__":
    asyncio.run(test_security_flow())
import asyncio
from langgraph_sdk import get_client

async def test_security_flow():
    # 1. Connect using Alice's Token
    alice_client = get_client(
        url="http://localhost:50614", 
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
        url="http://localhost:50614", 
        headers={"Authorization": "Bearer bob-secure-token"}
    )
    
    # Try looking for Alice's specific thread via Bob's client
    try:
        visible_threads = await bob_client.threads.search()
        thread_ids = [t["thread_id"] for t in visible_threads]
        print(f"Bob sees these threads: {thread_ids}") # Will not show Alice's thread ID
    except Exception as e:
        print(f"Bob access rejected: {e}")

if __name__ == "__main__":
    asyncio.run(test_security_flow())
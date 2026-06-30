# Secure LangGraph Agent Project - Testing Guide

This project demonstrates how to implement and validate production-grade security patterns in LangGraph Cloud and local environments. It covers **Custom Authentication (AuthN)**, **Multi-Tenant Data Isolation (AuthZ)**, and **Secure Agent State Propagation**.

## Project Security Architecture

The project uses a two-layer security validation setup:

1. **The Control Plane (Authentication & Authorization):** A custom authentication middleware inspects the incoming request headers, validates identity tokens, and applies dynamic database filters to isolate threads by user.
2. **The Execution Plane (State Propagation):** Validated user contexts are securely injected into the graph configuration (`config`), allowing downstream nodes and tools to access credentials securely without trusting client-side inputs.

---

## Prerequisites

Before running the test suite, ensure you have the following installed on your machine:
* **Python 3.11+**
* **uv** (Recommended Python package manager and runner) or **Poetry**
* **LangGraph CLI** (installed automatically via `uvx`)

---

## Setup Instructions

1. **Clone and Navigate to the Project Root:**
   $ cd secure-agent-project

2. **Install Dependencies:**
   If using `uv`, dependencies will be managed automatically during runtime. To install explicitly:
   $ uv pip install -e .

3. **Environment Configuration:**
   Create a `.env` file in the project root. Add your `OPENAI_API_KEY` (or your preferred LLM provider credentials):
   OPENAI_API_KEY=your_api_key_here

---

## Step-by-Step Testing Guide

Testing a security-hardened LangGraph setup requires a **two-terminal workflow**: one terminal serves the backend graph instance, and the second terminal acts as the client client running verification requests.

### Step 1: Start the LangGraph Server (Terminal 1)

Boot up the local development server. This server dynamically compiles your graph and attaches your security middleware located in `src/security/auth.py`.

$ uvx --from "langgraph-cli[inmem]" langgraph dev

Look for the confirmation message in your terminal output:
   🚀 Ready!
   API: http://localhost:2024
   Studio: [https://smith.langchain.com/studio/?baseUrl=http://localhost:2024](https://smith.langchain.com/studio/?baseUrl=http://localhost:2024)

*Leave this terminal window open and running.*

### Step 2: Run the Client Verification Script (Terminal 2)

Open a new terminal window, navigate back to your project root, and execute the security validation script:

$ uv run test.py

---

## Verifying the Test Results

When `test.py` runs, it tests two distinct user personas (`user_alice` and `user_bob`) to verify your system's defensive configurations. Check your terminal output to confirm the following three behaviors:

### 1. Successful Authentication (AuthN)
Alice sends a valid security token (`Bearer alice-secure-token`). The server securely registers her identity, permits thread creation, and grants graph execution access.
Expected Log:
   Alice created thread: 019f1867-7b9f-72d0-85f8-0c952a1d344b
   Alice Stream: {'messages': [{'role': 'assistant', 'content': 'Tool says: Accessing account storage for User: user_alice with verified access role: admin.'}]}

### 2. Multi-Tenant Cross-Access Prevention (AuthZ)
Bob connects using his token (`Bearer bob-secure-token`) and tries to discover active threads. Because the middleware automatically applies an ownership filter background check (`{"owner": "user_bob"}`), Bob is completely isolated. He cannot see or access Alice's thread.
Expected Log:
   Bob sees these threads: []

### 3. Invalid Token Rejection
If an unlisted or malformed token hits the endpoint, the security layer immediately throws an exception and halts execution before reaching the graph logic.
Expected Log:
   Access rejected: HTTP 401 Unauthorized: Unauthorized token

---

## Alternative: Testing in LangGraph Studio

You can also test the runtime graph execution visually using LangGraph Studio by clicking the local Studio link generated in Terminal 1.

* **How Studio is Handled:** LangGraph Studio requests bypass the token database via the `is_studio_user(request)` check in `auth.py`. 
* **Studio Persona:** In Studio, you will execute actions under the mock identity `studio_developer` with an `admin` role. Use this environment to debug node loops and state updates, but rely on `test.py` to test your end-to-end token validation logic.
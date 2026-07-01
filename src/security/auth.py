# By default, LangGraph Cloud relies on LangSmith API keys passed
# via the x-api-key header to verify incoming requests.
 
# For production web apps, you can bypass this default and handle Custom Authentication.

# Authentication:
# Using the native Auth primitives, you register a global authentication middleware handler.

# Any request failing this check is immediately blocked at the entry point with an HTTP error.
# See get_current_user() below for an example of how to implement a custom authentication flow.

# Authorization:
# Once a user is verified, you must prevent them from interacting
# with threads, assistants, or cron jobs that belong to someone else.
# LangGraph provides fine-grained, decorator-driven event handlers
# to manage resource-level access control.

# You can apply logic globally or drill down to specific resources like threads.
# See secure_thread isolation() below for an example of how to implement a custom authorization flow.

from langgraph_sdk.auth import Auth, is_studio_user

# Mock database of accepted bearer tokens for local validation testing
VALID_TOKENS = {
    "alice-secure-token": {"id": "user_alice", "role": "admin"},
    "bob-secure-token": {"id": "user_bob", "role": "viewer"}
}

auth = Auth()

@auth.authenticate
async def get_current_user(authorization: str | None) -> Auth.types.MinimalUserDict:
    """
    Step 1: Authenticate the incoming request header (AuthN).
    Extracts the Bearer token and resolves the user's profile.
    """
    if not authorization:
        raise Auth.exceptions.HTTPException(status_code=401, detail="Missing Authorization Header")
        
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise ValueError()
    except ValueError:
        raise Auth.exceptions.HTTPException(status_code=401, detail="Invalid token format. Use 'Bearer <token>'")

    if token not in VALID_TOKENS:
        raise Auth.exceptions.HTTPException(status_code=401, detail="Unauthorized token")
        
    user_data = VALID_TOKENS[token]
    
    # Custom attributes passed here become available inside config["configurable"]["langgraph_auth_user"]
    return {
        "identity": user_data["id"],
        "user_role": user_data["role"]
    }

@auth.on.threads
async def secure_thread_isolation(ctx: Auth.types.AuthContext, value: dict) -> dict:
    """
    Step 2: Enforce multi-tenant resource data isolation (AuthZ).
    Stamps metadata on creation and forces a filter match on read/search.
    """
    # Allow LangSmith Studio to view threads unrestricted during local debugging
    if is_studio_user(ctx.user):
        return {}
        
    user_id = ctx.user.identity
    
    # Inject an ownership filter so this user can only see or query their own threads
    filters = {"owner": user_id}
    metadata = value.setdefault("metadata", {})
    metadata.update(filters)
    
    return filters
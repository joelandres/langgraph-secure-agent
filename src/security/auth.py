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
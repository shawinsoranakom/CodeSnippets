async def mcp_oauth_login(
    request: MCPOAuthLoginRequest,
    user_id: Annotated[str, Security(get_user_id)],
) -> MCPOAuthLoginResponse:
    """
    Discover OAuth metadata from the MCP server and return a login URL.

    1. Discovers the protected-resource metadata (RFC 9728)
    2. Fetches the authorization server metadata (RFC 8414)
    3. Performs Dynamic Client Registration (RFC 7591) if available
    4. Returns the authorization URL for the frontend to open in a popup
    """
    # Validate URL to prevent SSRF — blocks loopback and private IP ranges.
    try:
        await validate_url_host(request.server_url)
    except ValueError as e:
        raise fastapi.HTTPException(status_code=400, detail=f"Invalid server URL: {e}")

    # Normalize the URL so that credentials stored here are matched consistently
    # by auto_lookup_mcp_credential (which also uses normalized URLs).
    server_url = normalize_mcp_url(request.server_url)
    client = MCPClient(server_url)

    # Step 1: Discover protected-resource metadata (RFC 9728)
    protected_resource = await client.discover_auth()

    metadata: dict[str, Any] | None = None

    if protected_resource and protected_resource.get("authorization_servers"):
        auth_server_url = protected_resource["authorization_servers"][0]
        resource_url = protected_resource.get("resource", server_url)

        # Validate the auth server URL from metadata to prevent SSRF.
        try:
            await validate_url_host(auth_server_url)
        except ValueError as e:
            raise fastapi.HTTPException(
                status_code=400,
                detail=f"Invalid authorization server URL in metadata: {e}",
            )

        # Step 2a: Discover auth-server metadata (RFC 8414)
        metadata = await client.discover_auth_server_metadata(auth_server_url)
    else:
        # Fallback: Some MCP servers (e.g. Linear) are their own auth server
        # and serve OAuth metadata directly without protected-resource metadata.
        # Don't assume a resource_url — omitting it lets the auth server choose
        # the correct audience for the token (RFC 8707 resource is optional).
        resource_url = None
        metadata = await client.discover_auth_server_metadata(server_url)

    if (
        not metadata
        or "authorization_endpoint" not in metadata
        or "token_endpoint" not in metadata
    ):
        raise fastapi.HTTPException(
            status_code=400,
            detail="This MCP server does not advertise OAuth support. "
            "You may need to provide an auth token manually.",
        )

    authorize_url = metadata["authorization_endpoint"]
    token_url = metadata["token_endpoint"]
    registration_endpoint = metadata.get("registration_endpoint")
    revoke_url = metadata.get("revocation_endpoint")

    # Step 3: Dynamic Client Registration (RFC 7591) if available
    frontend_base_url = settings.config.frontend_base_url
    if not frontend_base_url:
        raise fastapi.HTTPException(
            status_code=500,
            detail="Frontend base URL is not configured.",
        )
    redirect_uri = f"{frontend_base_url}/auth/integrations/mcp_callback"

    client_id = ""
    client_secret = ""
    if registration_endpoint:
        # Validate the registration endpoint to prevent SSRF via metadata.
        try:
            await validate_url_host(registration_endpoint)
        except ValueError:
            pass  # Skip registration, fall back to default client_id
        else:
            reg_result = await _register_mcp_client(
                registration_endpoint, redirect_uri, server_url
            )
            if reg_result:
                client_id = reg_result.get("client_id", "")
                client_secret = reg_result.get("client_secret", "")

    if not client_id:
        client_id = "autogpt-platform"

    # Step 4: Store state token with OAuth metadata for the callback
    scopes = (protected_resource or {}).get("scopes_supported") or metadata.get(
        "scopes_supported", []
    )
    state_token, code_challenge = await creds_manager.store.store_state_token(
        user_id,
        ProviderName.MCP.value,
        scopes,
        state_metadata={
            "authorize_url": authorize_url,
            "token_url": token_url,
            "revoke_url": revoke_url,
            "resource_url": resource_url,
            "server_url": server_url,
            "client_id": client_id,
            "client_secret": client_secret,
        },
    )

    # Step 5: Build and return the login URL
    handler = MCPOAuthHandler(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        authorize_url=authorize_url,
        token_url=token_url,
        resource_url=resource_url,
    )
    login_url = handler.get_login_url(
        scopes, state_token, code_challenge=code_challenge
    )

    return MCPOAuthLoginResponse(login_url=login_url, state_token=state_token)
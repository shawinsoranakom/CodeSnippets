async def mcp_store_token(
    request: MCPStoreTokenRequest,
    user_id: Annotated[str, Security(get_user_id)],
) -> CredentialsMetaResponse:
    """
    Store a manually provided bearer token as an MCP credential.

    Used by the Copilot MCPSetupCard when the server doesn't support the MCP
    OAuth discovery flow (returns 400 from /oauth/login).  Subsequent
    ``run_mcp_tool`` calls will automatically pick up the token via
    ``_auto_lookup_credential``.
    """
    token = request.token.get_secret_value().strip()
    if not token:
        raise fastapi.HTTPException(status_code=422, detail="Token must not be blank.")

    # Validate URL to prevent SSRF — blocks loopback and private IP ranges.
    try:
        await validate_url_host(request.server_url)
    except ValueError as e:
        raise fastapi.HTTPException(status_code=400, detail=f"Invalid server URL: {e}")

    # Normalize URL so trailing-slash variants match existing credentials.
    server_url = normalize_mcp_url(request.server_url)
    hostname = server_host(server_url)

    # Collect IDs of old credentials to clean up after successful create.
    old_cred_ids: list[str] = []
    try:
        old_creds = await creds_manager.store.get_creds_by_provider(
            user_id, ProviderName.MCP.value
        )
        old_cred_ids = [
            old.id
            for old in old_creds
            if isinstance(old, OAuth2Credentials)
            and normalize_mcp_url((old.metadata or {}).get("mcp_server_url", ""))
            == server_url
        ]
    except Exception:
        logger.debug("Could not query old MCP token credentials", exc_info=True)

    credentials = OAuth2Credentials(
        provider=ProviderName.MCP.value,
        title=f"MCP: {hostname}",
        access_token=SecretStr(token),
        scopes=[],
        metadata={"mcp_server_url": server_url},
    )
    await creds_manager.create(user_id, credentials)

    # Only delete old credentials after the new one is safely stored.
    for old_id in old_cred_ids:
        try:
            await creds_manager.store.delete_creds_by_id(user_id, old_id)
        except Exception:
            logger.debug("Could not clean up old MCP token credential", exc_info=True)

    return CredentialsMetaResponse(
        id=credentials.id,
        provider=credentials.provider,
        type=credentials.type,
        title=credentials.title,
        scopes=credentials.scopes,
        username=credentials.username,
        host=hostname,
    )
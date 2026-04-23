async def mcp_oauth_callback(
    request: MCPOAuthCallbackRequest,
    user_id: Annotated[str, Security(get_user_id)],
) -> CredentialsMetaResponse:
    """
    Exchange the authorization code for tokens and store the credential.

    The frontend calls this after receiving the OAuth code from the popup.
    On success, subsequent ``/discover-tools`` calls for the same server URL
    will automatically use the stored credential.
    """
    valid_state = await creds_manager.store.verify_state_token(
        user_id, request.state_token, ProviderName.MCP.value
    )
    if not valid_state:
        raise fastapi.HTTPException(
            status_code=400,
            detail="Invalid or expired state token.",
        )

    meta = valid_state.state_metadata
    frontend_base_url = settings.config.frontend_base_url
    if not frontend_base_url:
        raise fastapi.HTTPException(
            status_code=500,
            detail="Frontend base URL is not configured.",
        )
    redirect_uri = f"{frontend_base_url}/auth/integrations/mcp_callback"

    handler = MCPOAuthHandler(
        client_id=meta["client_id"],
        client_secret=meta.get("client_secret", ""),
        redirect_uri=redirect_uri,
        authorize_url=meta["authorize_url"],
        token_url=meta["token_url"],
        revoke_url=meta.get("revoke_url"),
        resource_url=meta.get("resource_url"),
    )

    try:
        credentials = await handler.exchange_code_for_tokens(
            request.code, valid_state.scopes, valid_state.code_verifier
        )
    except Exception as e:
        raise fastapi.HTTPException(
            status_code=400,
            detail=f"OAuth token exchange failed: {e}",
        )

    # Enrich credential metadata for future lookup and token refresh
    if credentials.metadata is None:
        credentials.metadata = {}
    credentials.metadata["mcp_server_url"] = meta["server_url"]
    credentials.metadata["mcp_client_id"] = meta["client_id"]
    credentials.metadata["mcp_client_secret"] = meta.get("client_secret", "")
    credentials.metadata["mcp_token_url"] = meta["token_url"]
    credentials.metadata["mcp_resource_url"] = meta.get("resource_url", "")

    hostname = server_host(meta["server_url"])
    credentials.title = f"MCP: {hostname}"

    # Remove old MCP credentials for the same server to prevent stale token buildup.
    try:
        old_creds = await creds_manager.store.get_creds_by_provider(
            user_id, ProviderName.MCP.value
        )
        for old in old_creds:
            if (
                isinstance(old, OAuth2Credentials)
                and (old.metadata or {}).get("mcp_server_url") == meta["server_url"]
            ):
                await creds_manager.store.delete_creds_by_id(user_id, old.id)
                logger.info(
                    "Removed old MCP credential %s for %s",
                    old.id,
                    server_host(meta["server_url"]),
                )
    except Exception:
        logger.debug("Could not clean up old MCP credentials", exc_info=True)

    await creds_manager.create(user_id, credentials)

    return CredentialsMetaResponse(
        id=credentials.id,
        provider=credentials.provider,
        type=credentials.type,
        title=credentials.title,
        scopes=credentials.scopes,
        username=credentials.username,
        host=credentials.metadata.get("mcp_server_url"),
    )
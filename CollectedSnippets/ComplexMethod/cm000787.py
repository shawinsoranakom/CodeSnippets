async def auto_lookup_mcp_credential(
    user_id: str, server_url: str
) -> OAuth2Credentials | None:
    """Look up the best stored MCP credential for *server_url*.

    The caller should pass a **normalized** URL (via :func:`normalize_mcp_url`)
    so the comparison with ``mcp_server_url`` in credential metadata matches.

    Returns the credential with the latest ``access_token_expires_at``, refreshed
    if needed, or ``None`` when no match is found.
    """
    from backend.data.model import OAuth2Credentials
    from backend.integrations.creds_manager import IntegrationCredentialsManager
    from backend.integrations.providers import ProviderName

    try:
        mgr = IntegrationCredentialsManager()
        mcp_creds = await mgr.store.get_creds_by_provider(
            user_id, ProviderName.MCP.value
        )
        # Collect all matching credentials and pick the best one.
        # Primary sort: latest access_token_expires_at (tokens with expiry
        # are preferred over non-expiring ones).  Secondary sort: last in
        # iteration order, which corresponds to the most recently created
        # row — this acts as a tiebreaker when multiple bearer tokens have
        # no expiry (e.g. after a failed old-credential cleanup).
        best: OAuth2Credentials | None = None
        for cred in mcp_creds:
            if (
                isinstance(cred, OAuth2Credentials)
                and (cred.metadata or {}).get("mcp_server_url") == server_url
            ):
                if best is None or (
                    (cred.access_token_expires_at or 0)
                    >= (best.access_token_expires_at or 0)
                ):
                    best = cred
        if best:
            best = await mgr.refresh_if_needed(user_id, best)
            logger.info("Auto-resolved MCP credential %s for %s", best.id, server_url)
        return best
    except Exception:
        logger.warning("Auto-lookup MCP credential failed", exc_info=True)
        return None
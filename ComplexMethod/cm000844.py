async def get_provider_token(user_id: str, provider: str) -> str | None:
    """Return the user's access token for *provider*, or ``None`` if not connected.

    OAuth2 tokens are preferred (refreshed if needed); API keys are the fallback.
    Found tokens are cached for _TOKEN_CACHE_TTL (5 min).  "Not connected" results
    are cached for _NULL_CACHE_TTL (60 s) to avoid a DB hit on every bash_exec
    command for users who haven't connected yet, while still picking up a
    newly-connected account within one minute.
    """
    cache_key = (user_id, provider)

    if cache_key in _null_cache:
        return None
    if cached := _token_cache.get(cache_key):
        return cached

    manager = _manager
    try:
        creds_list = await manager.store.get_creds_by_provider(user_id, provider)
    except Exception:
        logger.warning(
            "Failed to fetch %s credentials for user %s",
            provider,
            user_id,
            exc_info=True,
        )
        return None

    # Pass 1: prefer OAuth2 (carry scope info, refreshable via token endpoint).
    # Sort so broader-scoped tokens come first: a token with "repo" scope covers
    # full git access, while a public-data-only token lacks push/pull permission.
    # lock=False — background injection; not worth a distributed lock acquisition.
    oauth2_creds = sorted(
        [c for c in creds_list if c.type == "oauth2"],
        key=lambda c: 0 if "repo" in (cast(OAuth2Credentials, c).scopes or []) else 1,
    )
    refresh_failed = False
    for creds in oauth2_creds:
        if creds.type == "oauth2":
            try:
                fresh = await manager.refresh_if_needed(
                    user_id, cast(OAuth2Credentials, creds), lock=False
                )
                token = fresh.access_token.get_secret_value()
            except Exception:
                logger.warning(
                    "Failed to refresh %s OAuth token for user %s; "
                    "discarding stale token to force re-auth",
                    provider,
                    user_id,
                    exc_info=True,
                )
                # Do NOT fall back to the stale token — it is likely expired
                # or revoked.  Returning None forces the caller to re-auth,
                # preventing the LLM from receiving a non-functional token.
                refresh_failed = True
                continue
            _token_cache[cache_key] = token
            return token

    # Pass 2: fall back to API key (no expiry, no refresh needed).
    for creds in creds_list:
        if creds.type == "api_key":
            token = cast(APIKeyCredentials, creds).api_key.get_secret_value()
            _token_cache[cache_key] = token
            return token

    # Only cache "not connected" when the user truly has no credentials for this
    # provider.  If we had OAuth credentials but refresh failed (e.g. transient
    # network error, event-loop mismatch), do NOT cache the negative result —
    # the next call should retry the refresh instead of being blocked for 60 s.
    if not refresh_failed:
        _null_cache[cache_key] = True
    return None
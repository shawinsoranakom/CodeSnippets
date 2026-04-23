async def get_github_user_git_identity(user_id: str) -> dict[str, str] | None:
    """Fetch the GitHub user's name and email for git committer env vars.

    Uses the ``/user`` GitHub API endpoint with the user's stored token.
    Returns a dict with ``GIT_AUTHOR_NAME``, ``GIT_AUTHOR_EMAIL``,
    ``GIT_COMMITTER_NAME``, and ``GIT_COMMITTER_EMAIL`` if the user has a
    connected GitHub account.  Returns ``None`` otherwise.

    Results are cached for 10 minutes; "not connected" results are cached for
    60 s (same as null-token cache).
    """
    if user_id in _gh_identity_null_cache:
        return None
    if cached := _gh_identity_cache.get(user_id):
        return cached

    token = await get_provider_token(user_id, "github")
    if not token:
        _gh_identity_null_cache[user_id] = True
        return None

    import aiohttp

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.github.com/user",
                headers={
                    "Authorization": f"token {token}",
                    "Accept": "application/vnd.github+json",
                },
                timeout=aiohttp.ClientTimeout(total=5),
            ) as resp:
                if resp.status != 200:
                    logger.warning(
                        "[git-identity] GitHub /user returned %s for user %s",
                        resp.status,
                        user_id,
                    )
                    return None
                data = await resp.json()
    except Exception as exc:
        logger.warning(
            "[git-identity] Failed to fetch GitHub profile for user %s: %s",
            user_id,
            exc,
        )
        return None

    name = data.get("name") or data.get("login") or "AutoGPT User"
    # GitHub may return email=null if the user has set their email to private.
    # Fall back to the noreply address GitHub generates for every account.
    email = data.get("email")
    if not email:
        gh_id = data.get("id", "")
        login = data.get("login", "user")
        email = f"{gh_id}+{login}@users.noreply.github.com"

    identity = {
        "GIT_AUTHOR_NAME": name,
        "GIT_AUTHOR_EMAIL": email,
        "GIT_COMMITTER_NAME": name,
        "GIT_COMMITTER_EMAIL": email,
    }
    _gh_identity_cache[user_id] = identity
    return identity
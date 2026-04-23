async def _restore_browser_state(
    session_name: str, user_id: str, session: ChatSession
) -> bool:
    """Restore browser state from workspace storage into a fresh daemon.

    Best-effort: errors are logged but never propagate to the tool response.
    Returns True on success (or no state to restore), False on failure.
    """
    try:
        manager = await get_workspace_manager(user_id, session.session_id)

        file_info = await manager.get_file_info_by_path(_STATE_FILENAME)
        if file_info is None:
            return True  # No saved state — first call or never saved

        state_bytes = await manager.read_file(_STATE_FILENAME)
        state = json.loads(state_bytes.decode("utf-8"))

        url = state.get("url", "")
        cookies = state.get("cookies", [])
        local_storage = state.get("local_storage", {})

        # Navigate first — starts daemon + sets the correct origin for cookies
        if url:
            # Validate the saved URL to prevent SSRF via stored redirect targets.
            try:
                await validate_url_host(url)
            except ValueError:
                logger.warning(
                    "[browser] State restore: blocked SSRF URL %s", url[:200]
                )
                return False

            rc, _, stderr = await _run(session_name, "open", url)
            if rc != 0:
                logger.warning(
                    "[browser] State restore: failed to open %s: %s",
                    url,
                    stderr[:200],
                )
                return False
            await _run(session_name, "wait", "--load", "load", timeout=15)

        # Restore cookies and localStorage in parallel via asyncio.gather.
        # Semaphore caps concurrent subprocess spawns so we don't overwhelm the
        # system when a session has hundreds of cookies.
        sem = asyncio.Semaphore(_RESTORE_CONCURRENCY)

        # Guard against pathological sites with thousands of cookies.
        if len(cookies) > _MAX_RESTORE_COOKIES:
            logger.debug(
                "[browser] State restore: capping cookies from %d to %d",
                len(cookies),
                _MAX_RESTORE_COOKIES,
            )
            cookies = cookies[:_MAX_RESTORE_COOKIES]

        async def _set_cookie(c: dict[str, Any]) -> None:
            name = c.get("name", "")
            value = c.get("value", "")
            domain = c.get("domain", "")
            path = c.get("path", "/")
            if not (name and domain):
                return
            async with sem:
                rc, _, stderr = await _run(
                    session_name,
                    "cookies",
                    "set",
                    name,
                    value,
                    "--domain",
                    domain,
                    "--path",
                    path,
                    timeout=5,
                )
            if rc != 0:
                logger.debug(
                    "[browser] State restore: cookie set failed for %s: %s",
                    name,
                    stderr[:100],
                )

        async def _set_storage(key: str, val: object) -> None:
            async with sem:
                rc, _, stderr = await _run(
                    session_name,
                    "storage",
                    "local",
                    "set",
                    key,
                    str(val),
                    timeout=5,
                )
            if rc != 0:
                logger.debug(
                    "[browser] State restore: localStorage set failed for %s: %s",
                    key,
                    stderr[:100],
                )

        await asyncio.gather(
            *[_set_cookie(c) for c in cookies],
            *[_set_storage(k, v) for k, v in local_storage.items()],
        )

        return True
    except Exception:
        logger.warning(
            "[browser] Failed to restore browser state for session %s",
            session_name,
            exc_info=True,
        )
        return False
async def _execute(
        self,
        user_id: str | None,
        session: ChatSession,
        url: str = "",
        wait_for: str = "networkidle",
        **kwargs: Any,
    ) -> ToolResponseBase:
        """Navigate to *url*, wait for the page to settle, and return a snapshot.

        The snapshot is an accessibility-tree listing of interactive elements.
        Note: for slow SPAs that never fully idle, the snapshot may reflect a
        partially-loaded state (the wait is best-effort).
        """
        url = url.strip()
        wait_for = wait_for or "networkidle"
        session_name = session.session_id

        if not url:
            return ErrorResponse(
                message="Please provide a URL to navigate to.",
                error="missing_url",
                session_id=session_name,
            )

        try:
            await validate_url_host(url)
        except ValueError as e:
            return ErrorResponse(
                message=str(e),
                error="blocked_url",
                session_id=session_name,
            )

        # Restore browser state from cloud if this is a different pod
        if user_id:
            await _ensure_session(session_name, user_id, session)

        # Navigate
        rc, _, stderr = await _run(session_name, "open", url)
        if rc != 0:
            logger.warning(
                "[browser_navigate] open failed for %s: %s", url, stderr[:300]
            )
            return ErrorResponse(
                message="Failed to navigate to URL.",
                error="navigation_failed",
                session_id=session_name,
            )

        # Wait for page to settle (best-effort: some SPAs never reach networkidle)
        wait_rc, _, wait_err = await _run(session_name, "wait", "--load", wait_for)
        if wait_rc != 0:
            logger.warning(
                "[browser_navigate] wait(%s) failed: %s", wait_for, wait_err[:300]
            )

        # Get current title and URL in parallel
        (_, title_out, _), (_, url_out, _) = await asyncio.gather(
            _run(session_name, "get", "title"),
            _run(session_name, "get", "url"),
        )

        snapshot = await _snapshot(session_name)

        result = BrowserNavigateResponse(
            message=f"Navigated to {url}",
            url=url_out.strip() or url,
            title=title_out.strip(),
            snapshot=snapshot,
            session_id=session_name,
        )

        # Persist browser state to cloud for cross-pod continuity
        if user_id:
            _fire_and_forget_save(session_name, user_id, session)

        return result
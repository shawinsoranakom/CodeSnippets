async def _execute(
        self,
        user_id: str | None,
        session: ChatSession,
        annotate: bool | str = True,
        filename: str = "screenshot.png",
        **kwargs: Any,
    ) -> ToolResponseBase:
        """Capture a PNG screenshot and upload it to the workspace.

        Handles string-to-bool coercion for *annotate* (OpenAI function-call
        payloads sometimes deliver ``"true"``/``"false"`` as strings).
        Returns a :class:`BrowserScreenshotResponse` with the workspace
        ``file_id`` the LLM should pass to ``read_workspace_file``.
        """
        raw_annotate = annotate
        if isinstance(raw_annotate, str):
            annotate = raw_annotate.strip().lower() in {"1", "true", "yes", "on"}
        else:
            annotate = bool(raw_annotate)
        filename = filename.strip()
        session_name = session.session_id

        # Restore browser state from cloud if this is a different pod
        if user_id:
            await _ensure_session(session_name, user_id, session)

        tmp_fd, tmp_path = tempfile.mkstemp(suffix=".png")
        os.close(tmp_fd)
        try:
            cmd_args = ["screenshot"]
            if annotate:
                cmd_args.append("--annotate")
            cmd_args.append(tmp_path)

            rc, _, stderr = await _run(session_name, *cmd_args)
            if rc != 0:
                logger.warning("[browser_screenshot] failed: %s", stderr[:300])
                return ErrorResponse(
                    message="Failed to take screenshot.",
                    error="screenshot_failed",
                    session_id=session_name,
                )

            with open(tmp_path, "rb") as f:
                png_bytes = f.read()

        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass  # Best-effort temp file cleanup; not critical if it fails.

        # Upload to workspace so the user can view it
        png_b64 = base64.b64encode(png_bytes).decode()

        # Import here to avoid circular deps — workspace_files imports from .models
        from .workspace_files import WorkspaceWriteResponse, WriteWorkspaceFileTool

        write_resp = await WriteWorkspaceFileTool()._execute(
            user_id=user_id,
            session=session,
            filename=filename,
            content_base64=png_b64,
        )

        if not isinstance(write_resp, WorkspaceWriteResponse):
            return ErrorResponse(
                message="Screenshot taken but failed to save to workspace.",
                error="workspace_write_failed",
                session_id=session_name,
            )

        result = BrowserScreenshotResponse(
            message=f"Screenshot saved to workspace as '{filename}'. Use read_workspace_file with file_id='{write_resp.file_id}' to retrieve it.",
            file_id=write_resp.file_id,
            filename=filename,
            session_id=session_name,
        )

        # Persist browser state to cloud for cross-pod continuity
        if user_id:
            _fire_and_forget_save(session_name, user_id, session)

        return result
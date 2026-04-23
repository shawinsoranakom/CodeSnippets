async def _execute(
        self,
        user_id: str | None,
        session: ChatSession,
        path: str = "",
        **kwargs,
    ) -> ToolResponseBase:
        """Fetch full content of a documentation page.

        Args:
            user_id: User ID (not required for docs)
            session: Chat session
            path: Path to the documentation file

        Returns:
            DocPageResponse: Full document content
            ErrorResponse: Error message
        """
        path = path.strip()
        session_id = session.session_id if session else None

        if not path:
            return ErrorResponse(
                message="Please provide a documentation path.",
                error="Missing path parameter",
                session_id=session_id,
            )

        # Sanitize path to prevent directory traversal
        if ".." in path or path.startswith("/"):
            return ErrorResponse(
                message="Invalid documentation path.",
                error="invalid_path",
                session_id=session_id,
            )

        docs_root = self._get_docs_root()
        full_path = docs_root / path

        if not full_path.exists():
            return ErrorResponse(
                message=f"Documentation page not found: {path}",
                error="not_found",
                session_id=session_id,
            )

        # Ensure the path is within docs root
        try:
            full_path.resolve().relative_to(docs_root.resolve())
        except ValueError:
            return ErrorResponse(
                message="Invalid documentation path.",
                error="invalid_path",
                session_id=session_id,
            )

        try:
            content = full_path.read_text(encoding="utf-8")
            title = self._extract_title(content, path)

            return DocPageResponse(
                message=f"Retrieved documentation page: {title}",
                title=title,
                path=path,
                content=content,
                doc_url=self._make_doc_url(path),
                session_id=session_id,
            )

        except Exception as e:
            logger.error(f"Failed to read documentation page {path}: {e}")
            return ErrorResponse(
                message=f"Failed to read documentation page: {str(e)}",
                error="read_failed",
                session_id=session_id,
            )
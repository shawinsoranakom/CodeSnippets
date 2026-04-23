async def _execute(
        self,
        user_id: str | None,
        session: ChatSession,
        **kwargs: Any,
    ) -> ToolResponseBase:
        del user_id
        raw_todos = kwargs.get("todos")
        if raw_todos is None:
            return ErrorResponse(
                message="`todos` is required.",
                session_id=session.session_id,
            )
        if not isinstance(raw_todos, list):
            return ErrorResponse(
                message="`todos` must be an array.",
                session_id=session.session_id,
            )

        try:
            parsed = [TodoItem.model_validate(item) for item in raw_todos]
        except Exception as exc:
            return ErrorResponse(
                message=f"Invalid todo entry: {exc}",
                session_id=session.session_id,
            )

        in_progress = sum(1 for t in parsed if t.status == "in_progress")
        if in_progress > 1:
            return ErrorResponse(
                message=(
                    "Only one todo may be 'in_progress' at a time "
                    f"(found {in_progress})."
                ),
                session_id=session.session_id,
            )

        return TodoWriteResponse(
            message="Task list updated.",
            session_id=session.session_id,
            todos=parsed,
        )
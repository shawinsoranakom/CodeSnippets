def __init__(
        self,
        exception: BaseException,
        session_id: str | None = None,
        context_id: str | None = None,
        source: Source | None = None,
        trace_name: str | None = None,
        flow_id: UUID | str | None = None,
        session_metadata: dict | None = None,
    ) -> None:
        # This is done to avoid circular imports
        if exception.__class__.__name__ == "ExceptionWithMessageError" and exception.__cause__ is not None:
            exception = exception.__cause__

        plain_reason = self._format_plain_reason(exception)
        markdown_reason = self._format_markdown_reason(exception)
        # Get the sender ID
        if trace_name:
            match = re.search(r"\((.*?)\)", trace_name)
            if match:
                match.group(1)

        super().__init__(
            session_id=session_id,
            context_id=context_id,
            sender=source.display_name if source else None,
            sender_name=source.display_name if source else None,
            text=plain_reason,
            properties=Properties(
                text_color="red",
                background_color="red",
                edited=False,
                source=source,
                icon="error",
                allow_markdown=False,
                targets=[],
            ),
            category="error",
            error=True,
            content_blocks=[
                ContentBlock(
                    title="Error",
                    contents=[
                        ErrorContent(
                            type="error",
                            component=source.display_name if source else None,
                            field=str(exception.field) if hasattr(exception, "field") else None,
                            reason=markdown_reason,
                            solution=str(exception.solution) if hasattr(exception, "solution") else None,
                            traceback=traceback.format_exc(),
                        )
                    ],
                )
            ],
            flow_id=flow_id,
            session_metadata=session_metadata,
        )
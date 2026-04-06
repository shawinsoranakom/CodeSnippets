def __init__(
        self,
        errors: Sequence[Any],
        *,
        endpoint_ctx: EndpointContext | None = None,
    ) -> None:
        self._errors = errors
        self.endpoint_ctx = endpoint_ctx

        ctx = endpoint_ctx or {}
        self.endpoint_function = ctx.get("function")
        self.endpoint_path = ctx.get("path")
        self.endpoint_file = ctx.get("file")
        self.endpoint_line = ctx.get("line")
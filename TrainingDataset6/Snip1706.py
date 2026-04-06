def __init__(
        self,
        errors: Sequence[Any],
        *,
        body: Any = None,
        endpoint_ctx: EndpointContext | None = None,
    ) -> None:
        super().__init__(errors, endpoint_ctx=endpoint_ctx)
        self.body = body
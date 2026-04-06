def __init__(
        self,
        errors: Sequence[Any],
        *,
        endpoint_ctx: EndpointContext | None = None,
    ) -> None:
        super().__init__(errors, endpoint_ctx=endpoint_ctx)
def __init__(
        self,
        expression,
        kind,
        output_field=None,
        tzinfo=None,
        **extra,
    ):
        self.kind = kind
        super().__init__(expression, output_field=output_field, tzinfo=tzinfo, **extra)
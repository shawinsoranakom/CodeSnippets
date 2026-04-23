def __init__(
        self,
        expression,
        output_field=None,
        tzinfo=None,
        **extra,
    ):
        self.tzinfo = tzinfo
        super().__init__(expression, output_field=output_field, **extra)
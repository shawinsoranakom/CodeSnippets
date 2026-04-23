def __init__(
        self,
        value,
        output_field=None,
        *,
        config=None,
        invert=False,
        search_type="plain",
    ):
        if isinstance(value, LexemeCombinable):
            search_type = "raw"

        self.function = self.SEARCH_TYPES.get(search_type)
        if self.function is None:
            raise ValueError("Unknown search_type argument '%s'." % search_type)
        if not hasattr(value, "resolve_expression"):
            value = Value(value)
        expressions = (value,)
        self.config = SearchConfig.from_parameter(config)
        if self.config is not None:
            expressions = [self.config, *expressions]
        self.invert = invert
        super().__init__(*expressions, output_field=output_field)
def __init__(
        self,
        related_name=None,
        related_query_name=None,
        limit_choices_to=None,
        **kwargs,
    ):
        self._related_name = related_name
        self._related_query_name = related_query_name
        self._limit_choices_to = limit_choices_to
        super().__init__(**kwargs)
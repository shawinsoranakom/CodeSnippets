def __init__(
        self,
        field,
        to,
        related_name=None,
        related_query_name=None,
        limit_choices_to=None,
        symmetrical=True,
        through=None,
        through_fields=None,
        db_constraint=True,
    ):
        super().__init__(
            field,
            to,
            related_name=related_name,
            related_query_name=related_query_name,
            limit_choices_to=limit_choices_to,
        )

        if through and not db_constraint:
            raise ValueError("Can't supply a through model and db_constraint=False")
        self.through = through

        if through_fields and not through:
            raise ValueError("Cannot specify through_fields without a through model")
        self.through_fields = through_fields

        self.symmetrical = symmetrical
        self.db_constraint = db_constraint
def __init__(
        self,
        to,
        db_constraint=True,
        swappable=True,
        related_name=None,
        related_query_name=None,
        limit_choices_to=None,
        symmetrical=None,
        through=None,
        through_fields=None,
        db_table=None,
        **kwargs,
    ):
        try:
            to._meta
        except AttributeError:
            to = str(to)
        kwargs["rel"] = models.ManyToManyRel(
            self,
            to,
            related_name=related_name,
            related_query_name=related_query_name,
            limit_choices_to=limit_choices_to,
            symmetrical=(
                symmetrical
                if symmetrical is not None
                else (to == RECURSIVE_RELATIONSHIP_CONSTANT)
            ),
            through=through,
            through_fields=through_fields,
            db_constraint=db_constraint,
        )
        self.swappable = swappable
        self.db_table = db_table
        if kwargs["rel"].through is not None and self.db_table is not None:
            raise ValueError(
                "Cannot specify a db_table if an intermediary model is used."
            )
        super().__init__(
            related_name=related_name,
            related_query_name=related_query_name,
            limit_choices_to=limit_choices_to,
            **kwargs,
        )
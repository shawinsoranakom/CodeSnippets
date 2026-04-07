def __init__(
        self,
        to,
        on_delete,
        related_name=None,
        related_query_name=None,
        limit_choices_to=None,
        parent_link=False,
        to_field=None,
        db_constraint=True,
        **kwargs,
    ):
        try:
            to._meta.model_name
        except AttributeError:
            if not isinstance(to, str):
                raise TypeError(
                    "%s(%r) is invalid. First parameter to ForeignKey must be "
                    "either a model, a model name, or the string %r"
                    % (
                        self.__class__.__name__,
                        to,
                        RECURSIVE_RELATIONSHIP_CONSTANT,
                    )
                )
        else:
            # For backwards compatibility purposes, we need to *try* and set
            # the to_field during FK construction. It won't be guaranteed to
            # be correct until contribute_to_class is called. Refs #12190.
            to_field = to_field or (to._meta.pk and to._meta.pk.name)
        if not callable(on_delete):
            raise TypeError("on_delete must be callable.")

        kwargs["rel"] = self.rel_class(
            self,
            to,
            to_field,
            related_name=related_name,
            related_query_name=related_query_name,
            limit_choices_to=limit_choices_to,
            parent_link=parent_link,
            on_delete=on_delete,
        )
        kwargs.setdefault("db_index", True)

        super().__init__(
            to,
            on_delete,
            related_name=related_name,
            related_query_name=related_query_name,
            limit_choices_to=limit_choices_to,
            from_fields=[RECURSIVE_RELATIONSHIP_CONSTANT],
            to_fields=[to_field],
            **kwargs,
        )
        self.db_constraint = db_constraint
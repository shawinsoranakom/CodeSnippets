def resolve_expression(
        self, query=None, allow_joins=True, reuse=None, summarize=False, for_save=False
    ):
        c = super().resolve_expression(query, allow_joins, reuse, summarize, for_save)
        for field in c.get_source_fields():
            if not hasattr(field, "geom_type"):
                raise ValueError(
                    "Geospatial aggregates only allowed on geometry fields."
                )
        return c
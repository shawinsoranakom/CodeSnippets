def resolve_expression(self, *args, **kwargs):
        col = super().resolve_expression(*args, **kwargs)
        if col.contains_over_clause:
            raise NotSupportedError(
                f"Referencing outer query window expression is not supported: "
                f"{self.name}."
            )
        # FIXME: Rename possibly_multivalued to multivalued and fix detection
        # for non-multivalued JOINs (e.g. foreign key fields). This should take
        # into account only many-to-many and one-to-many relationships.
        col.possibly_multivalued = LOOKUP_SEP in self.name
        return col
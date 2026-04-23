def resolve_expression(self, *args, **kwargs):
        resolved = super().resolve_expression(*args, **kwargs)
        if type(self) is Subquery and self.template == Subquery.template:
            resolved.query.contains_subquery = True
            # Subquery is an unnecessary shim for a resolved query as it
            # complexifies the lookup's right-hand-side introspection.
            try:
                self.output_field
            except AttributeError:
                return resolved.query
            if self.output_field and type(self.output_field) is not type(
                resolved.query.output_field
            ):
                return ExpressionWrapper(resolved.query, output_field=self.output_field)
            return resolved.query
        return resolved
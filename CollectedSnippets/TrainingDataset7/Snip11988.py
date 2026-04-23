def _values(self, *fields, **expressions):
        clone = self._chain()
        if expressions:
            # RemovedInDjango70Warning: When the deprecation ends, deindent as:
            # clone = clone.annotate(**expressions)
            with warnings.catch_warnings(
                action="ignore", category=RemovedInDjango70Warning
            ):
                clone = clone.annotate(**expressions)
        clone._fields = fields
        clone.query.set_values(fields)
        return clone
def _model_indexes_sql(self, model):
        """
        Return a list of all index SQL statements (field indexes, Meta.indexes)
        for the specified model.
        """
        if not model._meta.managed or model._meta.proxy or model._meta.swapped:
            return []
        output = []
        for field in model._meta.local_fields:
            output.extend(self._field_indexes_sql(model, field))

        for index in model._meta.indexes:
            if (
                not index.contains_expressions
                or self.connection.features.supports_expression_indexes
            ):
                output.append(index.create_sql(model, self))
        return output
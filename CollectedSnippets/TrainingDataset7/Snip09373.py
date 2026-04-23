def remove_index(self, model, index):
        """Remove an index from a model."""
        if (
            index.contains_expressions
            and not self.connection.features.supports_expression_indexes
        ):
            return None
        self.execute(index.remove_sql(model, self))
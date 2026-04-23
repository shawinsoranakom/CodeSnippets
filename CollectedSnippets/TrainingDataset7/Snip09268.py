def bulk_batch_size(self, fields, objs):
        """
        Return the maximum allowed batch size for the backend. The fields
        are the fields going to be inserted in the batch, the objs contains
        all the objects to be inserted.
        """
        if self.connection.features.max_query_params is None or not fields:
            return len(objs)

        return self.connection.features.max_query_params // len(
            list(
                chain.from_iterable(
                    field.fields if isinstance(field, CompositePrimaryKey) else [field]
                    for field in fields
                )
            )
        )
def create_model(self, model):
        """
        Create a table and any accompanying indexes or unique constraints for
        the given `model`.
        """
        sql, params = self.table_sql(model)
        # Prevent using [] as params, in the case a literal '%' is used in the
        # definition on backends that don't support parametrized DDL.
        self.execute(sql, params or None)

        if self.connection.features.supports_comments:
            # Add table comment.
            if model._meta.db_table_comment:
                self.alter_db_table_comment(model, None, model._meta.db_table_comment)
            # Add column comments.
            if not self.connection.features.supports_comments_inline:
                for field in model._meta.local_fields:
                    if field.db_comment:
                        field_db_params = field.db_parameters(
                            connection=self.connection
                        )
                        field_type = field_db_params["type"]
                        self.execute(
                            *self._alter_column_comment_sql(
                                model, field, field_type, field.db_comment
                            )
                        )
        # Add any field index (deferred as SQLite _remake_table needs it).
        self.deferred_sql.extend(self._model_indexes_sql(model))

        # Make M2M tables
        for field in model._meta.local_many_to_many:
            if field.remote_field.through._meta.auto_created:
                self.create_model(field.remote_field.through)